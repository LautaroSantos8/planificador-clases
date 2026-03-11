"""
Views para gestión de documentos docentes (proyectos y planificaciones anuales)
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
import json
import logging
import os

from .models import DocumentoDocente, Alumno, NivelAlumno
from apps.docentes.models import AsignacionDocente
from apps.docentes.auth_views import get_user_from_token

logger = logging.getLogger(__name__)


def get_docente_from_request(request):
    """Obtiene el docente autenticado desde el token."""
    user = get_user_from_token(request)
    if user:
        return user
    return None


# =============================================================================
# DOCUMENTOS (Proyectos y Planificaciones Anuales)
# =============================================================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def documentos(request):
    """
    GET: Lista documentos del docente
    POST: Sube un nuevo documento
    """
    if request.method == "GET":
        return listar_documentos(request)
    else:
        return subir_documento(request)


def listar_documentos(request):
    """Lista los documentos del docente."""
    try:
        docente = get_docente_from_request(request)
        if not docente:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)
        
        asignacion_id = request.GET.get("asignacion_id")
        tipo = request.GET.get("tipo")  # proyecto | planificacion_anual
        
        # Filtrar por asignaciones del docente
        documentos = DocumentoDocente.objects.filter(
            asignacion__docente=docente
        ).select_related('asignacion', 'asignacion__materia')
        
        if asignacion_id:
            documentos = documentos.filter(asignacion_id=asignacion_id)
        
        if tipo:
            documentos = documentos.filter(tipo=tipo)
        
        data = []
        for doc in documentos:
            data.append({
                "id": doc.id,
                "titulo": doc.titulo,
                "tipo": doc.tipo,
                "tipo_display": doc.get_tipo_display(),
                "descripcion": doc.descripcion,
                "asignacion_id": doc.asignacion.id,
                "asignacion_nombre": f"{doc.asignacion.grado}° {doc.asignacion.division} - {doc.asignacion.materia.nombre}",
                "archivo_nombre": os.path.basename(doc.archivo.name) if doc.archivo else None,
                "procesado": doc.procesado,
                "chunks_generados": doc.chunks_generados,
                "created_at": doc.created_at.isoformat(),
            })
        
        return JsonResponse({"success": True, "documentos": data})
        
    except Exception as e:
        logger.error(f"Error en listar_documentos: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
def subir_documento(request):
    """Sube un nuevo documento y lo procesa para RAG."""
    try:
        docente = get_docente_from_request(request)
        if not docente:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)
        
        # Obtener datos del formulario
        titulo = request.POST.get("titulo")
        tipo = request.POST.get("tipo")
        descripcion = request.POST.get("descripcion", "")
        asignacion_id = request.POST.get("asignacion_id")
        archivo = request.FILES.get("archivo")
        
        # Validaciones
        if not titulo or not tipo or not asignacion_id or not archivo:
            return JsonResponse({
                "success": False, 
                "error": "Faltan campos requeridos: titulo, tipo, asignacion_id, archivo"
            }, status=400)
        
        if tipo not in ['proyecto', 'planificacion_anual']:
            return JsonResponse({
                "success": False,
                "error": "Tipo debe ser 'proyecto' o 'planificacion_anual'"
            }, status=400)
        
        # Verificar extensión
        extension = os.path.splitext(archivo.name)[1].lower()
        if extension not in ['.docx', '.pdf', '.xlsx']:
            return JsonResponse({
                "success": False,
                "error": "Formato no soportado. Use .docx, .pdf o .xlsx"
            }, status=400)
        
        # Verificar que la asignación pertenece al docente
        try:
            asignacion = AsignacionDocente.objects.get(id=asignacion_id, docente=docente)
        except AsignacionDocente.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Asignación no encontrada"
            }, status=404)
        
        # Crear documento
        documento = DocumentoDocente.objects.create(
            titulo=titulo,
            tipo=tipo,
            descripcion=descripcion,
            asignacion=asignacion,
            archivo=archivo,
        )
        
        # Procesar documento para RAG (en background sería ideal, pero lo hacemos sync por ahora)
        try:
            procesar_documento_para_rag(documento)
        except Exception as e:
            logger.error(f"Error procesando documento {documento.id}: {str(e)}")
            documento.error_procesamiento = str(e)
            documento.save()
        
        return JsonResponse({
            "success": True,
            "documento": {
                "id": documento.id,
                "titulo": documento.titulo,
                "tipo": documento.tipo,
                "procesado": documento.procesado,
                "chunks_generados": documento.chunks_generados,
            }
        })
        
    except Exception as e:
        logger.error(f"Error en subir_documento: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def eliminar_documento(request, documento_id):
    """Elimina un documento y sus chunks de ChromaDB."""
    try:
        docente = get_docente_from_request(request)
        if not docente:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)
        
        try:
            documento = DocumentoDocente.objects.get(
                id=documento_id,
                asignacion__docente=docente
            )
        except DocumentoDocente.DoesNotExist:
            return JsonResponse({"success": False, "error": "Documento no encontrado"}, status=404)
        
        # Eliminar chunks de ChromaDB
        try:
            eliminar_chunks_de_chroma(documento)
        except Exception as e:
            logger.warning(f"Error eliminando chunks de ChromaDB: {str(e)}")
        
        # Eliminar archivo físico
        if documento.archivo:
            try:
                default_storage.delete(documento.archivo.name)
            except Exception as e:
                logger.warning(f"Error eliminando archivo: {str(e)}")
        
        documento.delete()
        
        return JsonResponse({"success": True, "message": "Documento eliminado"})
        
    except Exception as e:
        logger.error(f"Error en eliminar_documento: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# =============================================================================
# PROCESAMIENTO RAG
# =============================================================================

def procesar_documento_para_rag(documento: DocumentoDocente):
    """Procesa un documento y lo guarda en ChromaDB."""
    from utils.proyecto_processor import ProyectoProcessor, preparar_para_chroma
    from apps.ai.core.chroma import ChromaManager
    
    # Obtener ruta del archivo
    file_path = documento.archivo.path
    
    # Procesar documento
    processor = ProyectoProcessor(chunk_size=1500, chunk_overlap=200)
    
    chunks = processor.process_proyecto(
        file_path=file_path,
        docente_id=documento.asignacion.docente.id,
        institucion_id=documento.asignacion.docente.institucion.id if documento.asignacion.docente.institucion else 0,
        grado=str(documento.asignacion.grado),
        tipo="proyecto_aulico" if documento.tipo == "proyecto" else "planificacion_anual",
    )
    
    # Guardar contenido extraído
    documento.contenido = "\n\n".join([chunk.texto for chunk in chunks])
    
    # Preparar para ChromaDB
    documents, metadatas, ids = preparar_para_chroma(chunks)
    
    # Agregar documento_id a metadata para poder eliminar después
    for meta in metadatas:
        meta['documento_db_id'] = documento.id
    
    # Guardar en ChromaDB
    chroma = ChromaManager()
    chroma.add_to_proyectos(documents, metadatas, ids)
    
    # Actualizar documento
    documento.procesado = True
    documento.chunks_generados = len(chunks)
    documento.error_procesamiento = ""
    documento.save()
    
    return len(chunks)


def eliminar_chunks_de_chroma(documento: DocumentoDocente):
    """Elimina los chunks de un documento de ChromaDB."""
    from apps.ai.core.chroma import ChromaManager
    
    chroma = ChromaManager()
    
    # Buscar chunks por documento_db_id
    try:
        collection = chroma.proyectos_docentes
        results = collection.get(
            where={"documento_db_id": documento.id}
        )
        
        if results and results['ids']:
            collection.delete(ids=results['ids'])
            
    except Exception as e:
        logger.error(f"Error eliminando chunks: {str(e)}")
        raise


# =============================================================================
# ALUMNOS (ya existente, mantenemos compatibilidad)
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def alumnos_por_grado_division(request):
    """Obtiene alumnos filtrados por grado y división.
    Crea NivelAlumno con LE por defecto si no existe para la asignación del docente.
    """
    grado = request.GET.get('grado')
    division = request.GET.get('division')
    
    if not grado or not division:
        return JsonResponse({
            'success': False,
            'error': 'Se requiere grado y division'
        }, status=400)
    
    try:
        # Obtener el docente autenticado para crear niveles por defecto
        docente = get_docente_from_request(request)

        alumnos = Alumno.objects.filter(
            grado=int(grado),
            division=division.upper()
        ).select_related('institucion')

        # Asignaciones del docente para este grado/división
        asignaciones_docente = []
        if docente:
            asignaciones_docente = list(
                AsignacionDocente.objects.filter(
                    docente=docente,
                    grado=int(grado),
                    division=division.upper()
                )
            )
            # Crear NivelAlumno con LE por defecto para cada alumno/asignación que no tenga
            for alumno in alumnos:
                for asignacion in asignaciones_docente:
                    NivelAlumno.objects.get_or_create(
                        alumno=alumno,
                        asignacion=asignacion,
                        defaults={'nivel': 'LE'}
                    )
        
        alumnos_data = []
        for alumno in alumnos:
            niveles = {}
            for nivel in alumno.niveles.select_related('asignacion', 'asignacion__materia'):
                materia_id = str(nivel.asignacion.materia.id)
                niveles[materia_id] = nivel.nivel
            
            alumnos_data.append({
                'id': alumno.id,
                'nombre': alumno.nombre,
                'apellido': alumno.apellido,
                'grado': alumno.grado,
                'division': alumno.division,
                'turno': alumno.turno,
                'observaciones': alumno.observaciones,
                'niveles': niveles,
                'institucion': alumno.institucion.nombre if alumno.institucion else None,
            })
        
        return JsonResponse({
            'success': True,
            'alumnos': alumnos_data,
            'total': len(alumnos_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def actualizar_nivel_alumno(request):
    """Actualiza el nivel de un alumno en una materia específica."""
    try:
        data = json.loads(request.body)
        alumno_id = data.get('alumno_id')
        materia_id = data.get('materia_id')
        nivel = data.get('nivel')
        motivo = data.get('motivo', '')
        
        if not all([alumno_id, materia_id, nivel]):
            return JsonResponse({
                'success': False,
                'error': 'Se requiere alumno_id, materia_id y nivel'
            }, status=400)
        
        if nivel not in ['NEE', 'LP', 'LE']:
            return JsonResponse({
                'success': False,
                'error': 'Nivel debe ser NEE, LP o LE'
            }, status=400)
        
        alumno = Alumno.objects.get(id=alumno_id)
        
        asignacion = AsignacionDocente.objects.filter(
            materia_id=materia_id,
            grado=alumno.grado,
            division=alumno.division
        ).first()
        
        if not asignacion:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró una asignación para esta materia y grado/división'
            }, status=404)
        
        nivel_obj, created = NivelAlumno.objects.get_or_create(
            alumno=alumno,
            asignacion=asignacion,
            defaults={'nivel': nivel}
        )
        
        if not created and nivel_obj.nivel != nivel:
            nivel_obj._motivo_cambio = motivo
            nivel_obj.nivel = nivel
            nivel_obj.save()
        
        return JsonResponse({
            'success': True,
            'nivel': {
                'alumno_id': alumno.id,
                'materia_id': materia_id,
                'nivel': nivel_obj.nivel,
                'created': created
            }
        })
        
    except Alumno.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Alumno no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def actualizar_observaciones(request):
    """Actualiza las observaciones de un alumno."""
    try:
        data = json.loads(request.body)
        alumno_id = data.get('alumno_id')
        observaciones = data.get('observaciones', '')
        
        if not alumno_id:
            return JsonResponse({
                'success': False,
                'error': 'Se requiere alumno_id'
            }, status=400)
        
        alumno = Alumno.objects.get(id=alumno_id)
        alumno.observaciones = observaciones
        alumno.save()
        
        return JsonResponse({
            'success': True,
            'alumno': {
                'id': alumno.id,
                'observaciones': alumno.observaciones
            }
        })
        
    except Alumno.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Alumno no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def niveles_por_alumno(request):
    """Obtiene todos los niveles de un alumno."""
    alumno_id = request.GET.get('alumno_id')
    
    if not alumno_id:
        return JsonResponse({
            'success': False,
            'error': 'Se requiere alumno_id'
        }, status=400)
    
    try:
        niveles = NivelAlumno.objects.filter(
            alumno_id=alumno_id
        ).select_related('asignacion', 'asignacion__materia')
        
        niveles_data = [{
            'materia_id': n.asignacion.materia.id,
            'materia_nombre': n.asignacion.materia.nombre,
            'nivel': n.nivel,
        } for n in niveles]
        
        return JsonResponse({
            'success': True,
            'niveles': niveles_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# =============================================================================
# ESTADÍSTICAS PERSONALIZADAS DEL DOCENTE
# =============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def estadisticas_docente(request):
    """
    Estadísticas personalizadas del docente autenticado.
    GET /api/planificacion/estadisticas/
    """
    try:
        from apps.planificacion.models import PlanificacionGenerada, NivelAlumno
        from django.db.models import Count, Q

        docente = get_docente_from_request(request)
        if not docente:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        asignaciones = AsignacionDocente.objects.filter(docente=docente)

        # Alumnos únicos del docente — usando Q filters para evitar union()
        grado_div_pares = list(asignaciones.values_list('grado', 'division').distinct())
        if grado_div_pares:
            from django.db.models import Q as Qfilter
            filtro = Qfilter()
            for g, d in grado_div_pares:
                filtro |= Qfilter(grado=int(g), division=d)
            total_alumnos = Alumno.objects.filter(filtro).count()
        else:
            total_alumnos = 0

        # Niveles de alumnos en asignaciones del docente
        niveles_qs = NivelAlumno.objects.filter(asignacion__docente=docente)
        nee = niveles_qs.filter(nivel='NEE').count()
        lp  = niveles_qs.filter(nivel='LP').count()
        le  = niveles_qs.filter(nivel='LE').count()

        # Planificaciones generadas
        planificaciones_qs = PlanificacionGenerada.objects.filter(asignacion__docente=docente)
        total_planificaciones = planificaciones_qs.count()
        feedback_positivo = planificaciones_qs.filter(fue_util=True).count()
        feedback_negativo = planificaciones_qs.filter(fue_util=False).count()

        # Documentos subidos
        total_documentos = DocumentoDocente.objects.filter(asignacion__docente=docente).count()

        # Última planificación generada
        ultima = planificaciones_qs.order_by('-created_at').first()
        ultima_fecha = ultima.created_at.strftime('%d/%m/%Y') if ultima else None

        return JsonResponse({
            "success": True,
            "estadisticas": {
                "asignaciones": asignaciones.count(),
                "total_alumnos": total_alumnos,
                "niveles": {"NEE": nee, "LP": lp, "LE": le},
                "planificaciones_generadas": total_planificaciones,
                "feedback_positivo": feedback_positivo,
                "feedback_negativo": feedback_negativo,
                "documentos_subidos": total_documentos,
                "ultima_planificacion": ultima_fecha,
            }
        })

    except Exception as e:
        logger.error(f"Error en estadisticas_docente: {str(e)}")
        return JsonResponse({"success": False, "error": "Error al obtener estadísticas"}, status=500)
