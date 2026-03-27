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
        tipo = request.POST.get("tipo", "proyecto")
        descripcion = request.POST.get("descripcion", "")
        asignacion_id = request.POST.get("asignacion_id")
        archivo = request.FILES.get("archivo")
        grado = request.POST.get("grado", "")
        materias_confirmadas = request.POST.get("materias_confirmadas", "")
        grados_lista = request.POST.get("grados_lista", "")

        if not titulo or not archivo:
            return JsonResponse({
                "success": False,
                "error": "Faltan campos requeridos: titulo, archivo"
            }, status=400)

        if tipo not in ['proyecto', 'planificacion_anual']:
            return JsonResponse({
                "success": False,
                "error": "Tipo debe ser 'proyecto' o 'planificacion_anual'"
            }, status=400)

        extension = os.path.splitext(archivo.name)[1].lower()
        if extension not in ['.docx', '.pdf', '.xlsx']:
            return JsonResponse({
                "success": False,
                "error": "Formato no soportado. Use .docx, .pdf o .xlsx"
            }, status=400)

        # Asignación es opcional ahora
        asignacion = None
        if asignacion_id:
            try:
                asignacion = AsignacionDocente.objects.get(id=asignacion_id, docente=docente)
            except AsignacionDocente.DoesNotExist:
                pass

        # Crear documento
        documento = DocumentoDocente.objects.create(
            titulo=titulo,
            tipo=tipo,
            descripcion=descripcion,
            asignacion=asignacion,
            archivo=archivo,
            grado=grado,
            grados_lista=grados_lista,
            materias_confirmadas=materias_confirmadas,
        )

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
                "materias_detectadas": documento.materias_detectadas,
                "grado": documento.grado,
            }
        })

    except Exception as e:
        logger.error(f"Error en subir_documento: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def analizar_documento(request):
    """
    Analiza un documento y detecta grado y materias sin guardarlo.
    Se usa para mostrar la previsualización antes de confirmar la carga.
    """
    try:
        docente = get_docente_from_request(request)
        if not docente:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        archivo = request.FILES.get("archivo")
        if not archivo:
            return JsonResponse({"success": False, "error": "Falta el archivo"}, status=400)

        extension = os.path.splitext(archivo.name)[1].lower()
        if extension not in ['.docx', '.pdf', '.xlsx']:
            return JsonResponse({
                "success": False,
                "error": "Formato no soportado. Use .docx, .pdf o .xlsx"
            }, status=400)

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
            for chunk in archivo.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            from utils.proyecto_processor import ProyectoProcessor
            processor = ProyectoProcessor()

            if extension == '.docx':
                texto = processor._extract_from_docx(tmp_path)
            elif extension == '.pdf':
                texto = processor._extract_from_pdf(tmp_path)
            else:
                texto = processor._extract_from_xlsx(tmp_path)

            texto = processor._limpiar_texto(texto)
            titulo = processor._extraer_titulo(texto)
            materias = processor._detectar_materias(texto)

            # Detectar grados con umbral mínimo de menciones
            import re
            grados_detectados = []
            texto_lower = texto.lower()

            patrones_todos = [
                r'\b1[°º]\s*a\s*6[°º]\b',
                r'\btodos\s*los\s*grados\b',
                r'\bsala.{0,10}(?:a\s*)?6[°º]\b',
            ]

            for patron in patrones_todos:
                if re.search(patron, texto_lower):
                    grados_detectados = ['1','2','3','4','5','6']
                    break

            if not grados_detectados:
                patrones_grado = [
                    (r'\b1[°º]\s*(?:grado|año)\b', '1'),
                    (r'\b2[°º]\s*(?:grado|año)\b', '2'),
                    (r'\b3[°º]\s*(?:grado|año)\b', '3'),
                    (r'\b4[°º]\s*(?:grado|año)\b', '4'),
                    (r'\b5[°º]\s*(?:grado|año)\b', '5'),
                    (r'\b6[°º]\s*(?:grado|año)\b', '6'),
                    (r'\bprimer\s*grado\b', '1'),
                    (r'\bsegundo\s*grado\b', '2'),
                    (r'\btercer\s*grado\b', '3'),
                    (r'\bcuarto\s*grado\b', '4'),
                    (r'\bquinto\s*grado\b', '5'),
                    (r'\bsexto\s*grado\b', '6'),
                ]

                conteo_grados = {}
                for patron, grado_val in patrones_grado:
                    count = len(re.findall(patron, texto_lower))
                    if count > 0:
                        conteo_grados[grado_val] = conteo_grados.get(grado_val, 0) + count

                # Solo incluir grados con 2+ menciones
                grados_detectados = sorted([g for g, c in conteo_grados.items() if c >= 2])

                # Si no detectó nada, usar el grado de la asignación actual
                if not grados_detectados:
                    from apps.docentes.models import AsignacionDocente
                    asignacion_id = request.POST.get("asignacion_id")
                    if asignacion_id:
                        try:
                            asignacion = AsignacionDocente.objects.get(id=asignacion_id, docente=docente)
                            grados_detectados = [str(asignacion.grado)]
                        except AsignacionDocente.DoesNotExist:
                            pass

        finally:
            import os as os_module
            os_module.unlink(tmp_path)
            
        return JsonResponse({
            "success": True,
            "titulo_detectado": titulo,
            "materias_detectadas": materias,
            "grados_detectados": grados_detectados,
        })

    except Exception as e:
        logger.error(f"Error analizando documento: {str(e)}")
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
    
    # Determinar grado — usar el del documento si existe, sino el de la asignación
    grado = documento.grado or (str(documento.asignacion.grado) if documento.asignacion else "todos")
    
    # Determinar materias confirmadas por el docente (si las hay)
    materias_param = None
    if documento.materias_confirmadas:
        materias_param = [m.strip() for m in documento.materias_confirmadas.split(',') if m.strip()]
    
    chunks = processor.process_proyecto(
        file_path=file_path,
        docente_id=documento.asignacion.docente.id if documento.asignacion else documento.docente.id,
        institucion_id=documento.asignacion.docente.institucion.id if documento.asignacion and documento.asignacion.docente.institucion else 0,
        grado=grado,
        materias=materias_param,
        tipo="proyecto_aulico" if documento.tipo == "proyecto" else "planificacion_anual",
    )
    
    # Guardar materias detectadas si no había confirmadas
    if not documento.materias_confirmadas and chunks:
        materias_detectadas = chunks[0].metadata.materias
        documento.materias_detectadas = ','.join(materias_detectadas)
        documento.grado = grado

    # Guardar contenido extraído
    documento.contenido = "\n\n".join([chunk.texto for chunk in chunks])
    
    # Preparar para ChromaDB
    documents, metadatas, ids = preparar_para_chroma(chunks)
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
                niveles[materia_id] = {
                    'nivel': nivel.nivel,
                    'nota_contextual': nivel.nota_contextual or '',
                }
            
            alumnos_data.append({
                'id': alumno.id,
                'nombre': alumno.nombre,
                'apellido': alumno.apellido,
                'grado': alumno.grado,
                'division': alumno.division,
                'turno': alumno.turno,
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
    """Actualiza el nivel de un alumno usando asignacion_id directo."""
    try:
        data = json.loads(request.body)
        alumno_id = data.get('alumno_id')
        asignacion_id = data.get('asignacion_id')
        nivel = data.get('nivel')
        motivo = data.get('motivo', '')
        
        if not all([alumno_id, asignacion_id, nivel]):
            return JsonResponse({
                'success': False,
                'error': 'Se requiere alumno_id, asignacion_id y nivel'
            }, status=400)
        
        if nivel not in ['NEE', 'LP', 'LE']:
            return JsonResponse({
                'success': False,
                'error': 'Nivel debe ser NEE, LP o LE'
            }, status=400)
        
        alumno = Alumno.objects.get(id=alumno_id)
        asignacion = AsignacionDocente.objects.get(id=asignacion_id)
        
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
                'asignacion_id': asignacion_id,
                'nivel': nivel_obj.nivel,
                'created': created
            }
        })
        
    except Alumno.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Alumno no encontrado'
        }, status=404)
    except AsignacionDocente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Asignación no encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def actualizar_observaciones(request):
    """Actualiza la nota contextual de un alumno en una asignación específica."""
    try:
        data = json.loads(request.body)
        alumno_id = data.get('alumno_id')
        asignacion_id = data.get('asignacion_id')
        nota_contextual = data.get('nota_contextual', '')
        
        if not alumno_id or not asignacion_id:
            return JsonResponse({
                'success': False,
                'error': 'Se requiere alumno_id y asignacion_id'
            }, status=400)
        
        nivel_obj = NivelAlumno.objects.get(
            alumno_id=alumno_id,
            asignacion_id=asignacion_id
        )
        nivel_obj.nota_contextual = nota_contextual
        nivel_obj.save()
        
        return JsonResponse({
            'success': True,
            'alumno_id': alumno_id,
            'asignacion_id': asignacion_id,
            'nota_contextual': nivel_obj.nota_contextual
        })
        
    except NivelAlumno.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'No se encontró el nivel del alumno para esta asignación'
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

        # Niveles por asignación
        niveles_por_asignacion = []
        for asig in asignaciones:
            qs = NivelAlumno.objects.filter(asignacion=asig)
            niveles_por_asignacion.append({
                'asignacion_id': asig.id,
                'label': f'{asig.materia.nombre} {asig.grado}°{asig.division}',
                'materia': asig.materia.nombre,
                'grado': asig.grado,
                'division': asig.division,
                'niveles': {
                    'NEE': qs.filter(nivel='NEE').count(),
                    'LP':  qs.filter(nivel='LP').count(),
                    'LE':  qs.filter(nivel='LE').count(),
                }
            })
        # Totales globales (para compatibilidad)
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
                "niveles_por_asignacion": niveles_por_asignacion,
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
