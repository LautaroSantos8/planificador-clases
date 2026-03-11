"""
Views para gestión de asignaciones de docentes
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .models import AsignacionDocente, Materia, Docente, Institucion
from .auth_views import get_user_from_token

logger = logging.getLogger(__name__)


def get_docente_from_request(request):
    """Obtiene el docente autenticado desde el token."""
    # Primero intentar con token
    user = get_user_from_token(request)
    if user:
        return user
    
    # Fallback para desarrollo: usar docente_id del request
    if request.method == 'GET':
        docente_id = request.GET.get('docente_id')
    else:
        try:
            data = json.loads(request.body)
            docente_id = data.get('docente_id')
        except:
            docente_id = None
    
    if docente_id:
        try:
            return Docente.objects.get(id=docente_id)
        except Docente.DoesNotExist:
            return None
    
    return None


@csrf_exempt
@require_http_methods(["GET", "POST"])
def asignaciones(request):
    """
    GET: Obtiene las asignaciones del docente autenticado
    POST: Crea una nueva asignación
    """
    if request.method == "GET":
        return get_asignaciones(request)
    else:
        return create_asignacion(request)


def get_asignaciones(request):
    """Obtiene las asignaciones del docente."""
    try:
        docente = get_docente_from_request(request)
        
        if not docente:
            return JsonResponse({
                "success": False,
                "error": "No autenticado"
            }, status=401)
        
        asignaciones = AsignacionDocente.objects.filter(
            docente=docente
        ).select_related('materia')
        
        data = []
        for a in asignaciones:
            data.append({
                "id": a.id,
                "grado": str(a.grado),
                "division": a.division,
                "turno": a.turno,
                "turno_display": a.get_turno_display(),
                "materia_id": a.materia.id,
                "materia_nombre": a.materia.nombre,
            })
        
        return JsonResponse({
            "success": True,
            "asignaciones": data
        })
        
    except Exception as e:
        logger.error(f"Error en get_asignaciones: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Error al obtener asignaciones"
        }, status=500)


def create_asignacion(request):
    """Crea una nueva asignación."""
    try:
        data = json.loads(request.body)
        
        docente = get_docente_from_request(request)
        
        if not docente:
            return JsonResponse({
                "success": False,
                "error": "No autenticado"
            }, status=401)
        
        # Validar campos
        grado = data.get("grado")
        division = data.get("division", "A")
        turno = data.get("turno", "M")
        materia_nombre = data.get("materia_nombre")
        
        if not grado or not materia_nombre:
            return JsonResponse({
                "success": False,
                "error": "Grado y materia son requeridos"
            }, status=400)
        
        # Verificar institución
        if not docente.institucion:
            return JsonResponse({
                "success": False,
                "error": "El docente no tiene institución asignada"
            }, status=400)
        
        # Obtener o crear la materia
        materia, _ = Materia.objects.get_or_create(
            nombre=materia_nombre,
            institucion=docente.institucion
        )
        
        # Verificar si ya existe la asignación
        existe = AsignacionDocente.objects.filter(
            docente=docente,
            grado=int(grado),
            division=division.upper(),
            materia=materia
        ).exists()
        
        if existe:
            return JsonResponse({
                "success": False,
                "error": "Ya tenés esta asignación registrada"
            }, status=400)
        
        # Crear asignación
        asignacion = AsignacionDocente.objects.create(
            docente=docente,
            grado=int(grado),
            division=division.upper(),
            turno=turno,
            materia=materia
        )
        
        return JsonResponse({
            "success": True,
            "asignacion": {
                "id": asignacion.id,
                "grado": str(asignacion.grado),
                "division": asignacion.division,
                "turno": asignacion.turno,
                "turno_display": asignacion.get_turno_display(),
                "materia_id": materia.id,
                "materia_nombre": materia.nombre,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "JSON inválido"
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error en create_asignacion: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": f"Error al crear asignación: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def eliminar_asignacion(request, asignacion_id):
    """Elimina una asignación."""
    try:
        docente = get_docente_from_request(request)
        
        if not docente:
            return JsonResponse({
                "success": False,
                "error": "No autenticado"
            }, status=401)
        
        # Buscar asignación del docente
        try:
            asignacion = AsignacionDocente.objects.get(
                id=asignacion_id,
                docente=docente
            )
        except AsignacionDocente.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Asignación no encontrada"
            }, status=404)
        
        asignacion.delete()
        
        return JsonResponse({
            "success": True,
            "message": "Asignación eliminada"
        })
        
    except Exception as e:
        logger.error(f"Error en eliminar_asignacion: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Error al eliminar asignación"
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def materias_disponibles(request):
    """Obtiene las materias disponibles para la institución del docente."""
    try:
        # Materias predefinidas comunes
        materias_comunes = [
            "Matemática",
            "Lengua",
            "Ciencias Naturales",
            "Ciencias Sociales",
            "Educación Física",
            "Música",
            "Plástica",
            "Tecnología",
            "Inglés",
        ]
        
        return JsonResponse({
            "success": True,
            "materias": materias_comunes
        })
        
    except Exception as e:
        logger.error(f"Error en materias_disponibles: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Error al obtener materias"
        }, status=500)
