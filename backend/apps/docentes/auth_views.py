from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
import json


@csrf_exempt
def login_view(request):
    """Endpoint para iniciar sesión. Devuelve un token de autenticación."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email y contraseña son requeridos'}, status=400)
        
        # Autenticar usando email como username
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Crear o obtener token
            token, created = Token.objects.get_or_create(user=user)
            
            return JsonResponse({
                'success': True,
                'token': token.key,
                'docente': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'institucion': user.institucion.nombre if user.institucion else None,
                    'institucion_id': user.institucion.id if user.institucion else None,
                }
            })
        else:
            return JsonResponse({'error': 'Credenciales inválidas'}, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def logout_view(request):
    """Endpoint para cerrar sesión. Elimina el token."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Obtener token del header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Token '):
        token_key = auth_header.split(' ')[1]
        try:
            token = Token.objects.get(key=token_key)
            token.delete()
            return JsonResponse({'success': True, 'message': 'Sesión cerrada'})
        except Token.DoesNotExist:
            pass
    
    return JsonResponse({'success': True, 'message': 'Sesión cerrada'})


@csrf_exempt
def profile_view(request):
    """Endpoint para obtener perfil del docente autenticado."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Obtener token del header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Token '):
        return JsonResponse({'error': 'Token no proporcionado'}, status=401)
    
    token_key = auth_header.split(' ')[1]
    
    try:
        token = Token.objects.get(key=token_key)
        user = token.user
        
        return JsonResponse({
            'success': True,
            'docente': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'institucion': user.institucion.nombre if user.institucion else None,
                'institucion_id': user.institucion.id if user.institucion else None,
            }
        })
    except Token.DoesNotExist:
        return JsonResponse({'error': 'Token inválido'}, status=401)


@csrf_exempt  
def registro_view(request):
    """Endpoint para registrar nuevo docente."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        from apps.docentes.models import Docente, Institucion
        
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        institucion_id = data.get('institucion_id')
        
        if not email or not password:
            return JsonResponse({'error': 'Email y contraseña son requeridos'}, status=400)
        
        # Verificar si ya existe
        if Docente.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Ya existe un docente con ese email'}, status=400)
        
        # Obtener institución
        institucion = None
        if institucion_id:
            try:
                institucion = Institucion.objects.get(id=institucion_id)
            except Institucion.DoesNotExist:
                pass
        
        # Crear docente
        docente = Docente.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            institucion=institucion,
        )
        
        # Crear token para el nuevo usuario
        token = Token.objects.create(user=docente)
        
        return JsonResponse({
            'success': True,
            'token': token.key,
            'docente': {
                'id': docente.id,
                'email': docente.email,
                'first_name': docente.first_name,
                'last_name': docente.last_name,
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def cambiar_password_view(request):
    """Endpoint para cambiar la contraseña del docente autenticado."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    user = get_user_from_token(request)
    if not user:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    try:
        data = json.loads(request.body)
        password_actual = data.get('password_actual')
        password_nuevo = data.get('password_nuevo')
        
        if not password_actual or not password_nuevo:
            return JsonResponse({'error': 'Contraseña actual y nueva son requeridas'}, status=400)
        
        if len(password_nuevo) < 4:
            return JsonResponse({'error': 'La contraseña nueva debe tener al menos 4 caracteres'}, status=400)
        
        # Verificar contraseña actual
        if not user.check_password(password_actual):
            return JsonResponse({'error': 'La contraseña actual es incorrecta'}, status=400)
        
        # Cambiar contraseña
        user.set_password(password_nuevo)
        user.save()
        
        # Renovar token
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        
        return JsonResponse({
            'success': True,
            'message': 'Contraseña cambiada correctamente',
            'token': token.key
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
        
def get_user_from_token(request):
    """
    Función auxiliar para obtener el usuario desde el token.
    Útil para usar en otras views.
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Token '):
        return None
    
    token_key = auth_header.split(' ')[1]
    
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None
