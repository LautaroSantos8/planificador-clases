"""
Views para el Asistente de Planificación Docente
API REST para interactuar con el planificador desde el frontend
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import logging
from datetime import datetime

from .core.planificador import PlanificadorDocente
from .core.chroma import ChromaManager
from apps.planificacion.models import PlanificacionGenerada
from apps.docentes.models import AsignacionDocente
from apps.docentes.auth_views import get_user_from_token
from utils.exportador import generar_pdf, generar_docx

logger = logging.getLogger(__name__)

# Instancia global del planificador (singleton pattern)
_planificador = None

def normalizar_texto(texto: str) -> str:
    """Normaliza texto: minúsculas y sin tildes."""
    if not texto:
        return texto
    import unicodedata
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

def normalizar_materia(materia: str) -> str:
    """Normaliza el nombre de materia al formato de la base."""
    if not materia:
        return None
    
    materia = normalizar_texto(materia)
    
    # Mapeo de variantes comunes
    mapeo = {
        "matematica": "matematicas",
        "lengua": "lengua",
        "ciencias naturales": "ciencias_naturales",
        "naturales": "ciencias_naturales",
        "ciencias sociales": "ciencias_sociales",
        "sociales": "ciencias_sociales",
    }
    
    return mapeo.get(materia, materia)

def get_planificador():
    """Obtiene o crea la instancia del planificador."""
    global _planificador
    if _planificador is None:
        _planificador = PlanificadorDocente()
    return _planificador


@csrf_exempt
@require_http_methods(["POST"])
def consultar_asistente(request):
    """
    Endpoint principal para consultas al asistente.
    Ahora también guarda el historial en la base de datos.
    """
    try:
        # Parsear body
        data = json.loads(request.body)
        
        # Validar campos requeridos
        consulta = data.get("consulta", "").strip()
        if not consulta:
            return JsonResponse({
                "success": False,
                "error": "La consulta no puede estar vacía"
            }, status=400)
        
        # Obtener datos del docente autenticado desde el token
        docente = get_user_from_token(request)
        if docente:
            docente_id = docente.id
            nombre_docente = docente.get_full_name() or docente.email
            institucion = docente.institucion.nombre if docente.institucion else "Escuela Municipal Dr. Jorge Orgaz"
        else:
            # Para desarrollo/testing sin auth
            docente_id = data.get("docente_id", 1)
            nombre_docente = data.get("nombre_docente", "Docente")
            institucion = data.get("institucion", "Escuela Municipal Dr. Jorge Orgaz")
        
        # Obtener parámetros de la consulta
        grado = data.get("grado", "")
        # Convertir número de grado a texto legible para el LLM
        from apps.docentes.models import AsignacionDocente as AD
        grado_display = AD.grado_to_str(int(grado)) if grado and grado.lstrip('-').isdigit() else grado
        division = data.get("division", "A")
        division = data.get("division", "A")
        materia = data.get("materia", "")
        turno = data.get("turno", "Mañana")
        alumnos = data.get("alumnos", [])
        actividad_original = data.get("actividad_original", "")
        actividad_evaluar = data.get("actividad_evaluar", "")
        asignacion_id = data.get("asignacion_id")
        historial = data.get("historial", [])  # Lista de {role, content}
        
        # Validar grado y materia
        if not grado or not materia:
            return JsonResponse({
                "success": False,
                "error": "Grado y materia son requeridos"
            }, status=400)
        
        # Procesar consulta
        planificador = get_planificador()
        resultado = planificador.procesar_consulta(
            consulta=consulta,
            docente_id=docente_id,
            grado=grado_display,
            division=division,
            materia=materia,
            nombre_docente=nombre_docente,
            turno=turno,
            institucion=institucion,
            alumnos=alumnos,
            actividad_original=actividad_original,
            actividad_evaluar=actividad_evaluar,
            historial=historial,
        )
        
        # Guardar en historial si hay asignacion_id
        planificacion_id = None
        if asignacion_id and resultado.get("respuesta"):
            try:
                asignacion = AsignacionDocente.objects.get(id=asignacion_id)
                planificacion = PlanificacionGenerada.objects.create(
                    asignacion=asignacion,
                    prompt_original=consulta,
                    respuesta_ia=resultado["respuesta"],
                    actividades_json={
                        "tipo_consulta": resultado["tipo_consulta"],
                        "contexto_utilizado": resultado["contexto_utilizado"]
                    }
                )
                planificacion_id = planificacion.id
            except AsignacionDocente.DoesNotExist:
                logger.warning(f"Asignación {asignacion_id} no encontrada para guardar historial")
            except Exception as e:
                logger.error(f"Error guardando historial: {str(e)}")
        
        return JsonResponse({
            "success": True,
            "tipo_consulta": resultado["tipo_consulta"],
            "respuesta": resultado["respuesta"],
            "contexto_utilizado": resultado["contexto_utilizado"],
            "planificacion_id": planificacion_id,
            "error": resultado["error"]
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "JSON inválido en el body"
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error en consultar_asistente: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Error interno del servidor"
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def obtener_historial(request):
    """
    Obtiene el historial de conversaciones de una asignación.
    
    GET /api/ai/historial/?asignacion_id=1
    """
    try:
        asignacion_id = request.GET.get("asignacion_id")
        
        if not asignacion_id:
            return JsonResponse({
                "success": False,
                "error": "Se requiere asignacion_id"
            }, status=400)
        
        # Obtener las últimas 50 conversaciones de esta asignación
        planificaciones = PlanificacionGenerada.objects.filter(
            asignacion_id=asignacion_id
        ).order_by('created_at')[:50]
        
        historial = []
        for p in planificaciones:
            historial.append({
                "id": p.id,
                "role": "user",
                "content": p.prompt_original,
                "es_resumen": p.es_resumen,
                "created_at": p.created_at.isoformat()
            })
            historial.append({
                "id": p.id,
                "role": "assistant",
                "content": p.respuesta_ia,
                "es_resumen": p.es_resumen,
                "tipo_consulta": p.actividades_json.get("tipo_consulta") if p.actividades_json else None,
                "contexto": p.actividades_json.get("contexto_utilizado") if p.actividades_json else None,
                "fue_util": p.fue_util,
                "created_at": p.created_at.isoformat()
            })
        
        return JsonResponse({
            "success": True,
            "historial": historial,
            "total": len(planificaciones)
        })
        
    except Exception as e:
        logger.error(f"Error en obtener_historial: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Error al obtener historial"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def guardar_feedback(request):
    """
    Guarda el feedback del docente sobre una respuesta.
    
    POST /api/ai/feedback/
    
    Body:
    {
        "planificacion_id": 1,
        "fue_util": true,
        "feedback": "Muy útil, pero..."
    }
    """
    try:
        data = json.loads(request.body)
        
        planificacion_id = data.get("planificacion_id")
        fue_util = data.get("fue_util")
        feedback_texto = data.get("feedback", "")
        
        if not planificacion_id:
            return JsonResponse({
                "success": False,
                "error": "Se requiere planificacion_id"
            }, status=400)
        
        try:
            planificacion = PlanificacionGenerada.objects.get(id=planificacion_id)
            planificacion.fue_util = fue_util
            planificacion.feedback = feedback_texto
            planificacion.save()
            
            return JsonResponse({
                "success": True,
                "message": "Feedback guardado correctamente"
            })
            
        except PlanificacionGenerada.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Planificación no encontrada"
            }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "JSON inválido"
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error en guardar_feedback: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Error al guardar feedback"
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def mensaje_bienvenida(request):
    """
    Obtiene el mensaje de bienvenida del asistente.
    """
    try:
        planificador = get_planificador()
        mensaje = planificador.obtener_mensaje_bienvenida()
        
        return JsonResponse({
            "success": True,
            "mensaje": mensaje
        })
        
    except Exception as e:
        logger.error(f"Error en mensaje_bienvenida: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Error al obtener mensaje de bienvenida"
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def estadisticas_rag(request):
    """
    Obtiene estadísticas de las colecciones en ChromaDB.
    """
    try:
        chroma = ChromaManager()
        stats = chroma.get_collection_stats()
        
        return JsonResponse({
            "success": True,
            "estadisticas": stats
        })
        
    except Exception as e:
        logger.error(f"Error en estadisticas_rag: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Error al obtener estadísticas"
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Endpoint de health check para verificar que el servicio está activo.
    """
    services = {
        "chroma": False,
        "gemini": False
    }
    
    # Verificar ChromaDB
    try:
        chroma = ChromaManager()
        chroma.get_collection_stats()
        services["chroma"] = True
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {str(e)}")
    
    # Verificar Gemini (solo que se puede inicializar)
    try:
        planificador = get_planificador()
        if planificador.model:
            services["gemini"] = True
    except Exception as e:
        logger.error(f"Gemini health check failed: {str(e)}")
    
    status = "ok" if all(services.values()) else "degraded"
    
    return JsonResponse({
        "status": status,
        "services": services
    })


@csrf_exempt
@require_http_methods(["POST"])
def buscar_curricula(request):
    """
    Endpoint para buscar en la currícula sin generar respuesta con IA.
    """
    try:
        data = json.loads(request.body)
        
        query = data.get("query", "").strip()
        if not query:
            return JsonResponse({
                "success": False,
                "error": "Query no puede estar vacío"
            }, status=400)
        
        grado = data.get("grado")
        materia = data.get("materia")
        n_results = min(data.get("n_results", 5), 10)
        
        chroma = ChromaManager()
        
        # Buscar en provincial (progresiones)
        resultados_provincial = chroma.search_provincial(
            query=query,
            provincia=normalizar_texto("Córdoba"),
            materia=normalizar_materia(materia) if materia else None,
            grado=grado,
            n_results=n_results
        )
        
        # Formatear resultados
        resultados = []
        if resultados_provincial.get("documents") and resultados_provincial["documents"][0]:
            for i, doc in enumerate(resultados_provincial["documents"][0]):
                meta = {}
                if resultados_provincial.get("metadatas") and resultados_provincial["metadatas"][0]:
                    meta = resultados_provincial["metadatas"][0][i]
                
                resultados.append({
                    "contenido": doc[:500] + "..." if len(doc) > 500 else doc,
                    "fuente": "curricula_provincial",
                    "documento": meta.get("documento", ""),
                    "grado": meta.get("grado", ""),
                    "materia": meta.get("materia", "")
                })
        
        return JsonResponse({
            "success": True,
            "resultados": resultados,
            "total": len(resultados)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "JSON inválido"
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error en buscar_curricula: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Error al buscar en currícula"
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def exportar_planificacion(request):
    """
    Exporta una planificación guardada como PDF o DOCX.

    GET /api/ai/exportar/?planificacion_id=1&formato=pdf
    GET /api/ai/exportar/?planificacion_id=1&formato=docx
    """
    try:
        planificacion_id = request.GET.get("planificacion_id")
        formato = request.GET.get("formato", "pdf").lower()

        if not planificacion_id:
            return JsonResponse({"success": False, "error": "Se requiere planificacion_id"}, status=400)

        if formato not in ("pdf", "docx"):
            return JsonResponse({"success": False, "error": "Formato inválido. Use 'pdf' o 'docx'"}, status=400)

        try:
            planificacion = PlanificacionGenerada.objects.select_related(
                "asignacion__materia",
                "asignacion__docente",
            ).get(id=planificacion_id)
        except PlanificacionGenerada.DoesNotExist:
            return JsonResponse({"success": False, "error": "Planificación no encontrada"}, status=404)

        asignacion   = planificacion.asignacion
        docente      = asignacion.docente
        nombre_doc   = docente.get_full_name() or docente.email
        from apps.docentes.models import AsignacionDocente as AD
        grado = AD.grado_to_str(asignacion.grado)
        division     = asignacion.division
        materia      = asignacion.materia.nombre
        consulta     = planificacion.prompt_original
        respuesta_md = planificacion.respuesta_ia
        fecha        = planificacion.created_at

        nombre_archivo = (
            f"planificacion_{grado}{division}_{materia.replace(' ', '_')}"
            f"_{fecha.strftime('%Y%m%d')}"
        )

        if formato == "pdf":
            contenido = generar_pdf(
                respuesta_md=respuesta_md,
                nombre_docente=nombre_doc,
                grado=grado,
                division=division,
                materia=materia,
                consulta_original=consulta,
                fecha=fecha,
            )
            response = HttpResponse(contenido, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}.pdf"'

        else:  # docx
            contenido = generar_docx(
                respuesta_md=respuesta_md,
                nombre_docente=nombre_doc,
                grado=grado,
                division=division,
                materia=materia,
                consulta_original=consulta,
                fecha=fecha,
            )
            response = HttpResponse(
                contenido,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}.docx"'

        response["Access-Control-Expose-Headers"] = "Content-Disposition"
        return response

    except Exception as e:
        logger.error(f"Error en exportar_planificacion: {str(e)}")
        return JsonResponse({"success": False, "error": "Error al exportar"}, status=500)
