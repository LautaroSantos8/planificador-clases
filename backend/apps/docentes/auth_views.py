from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import status

import json
import logging

logger = logging.getLogger(__name__)
Docente = get_user_model()


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

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
        logger.error(f"Error en login: {e}", exc_info=True)
        return JsonResponse({'error': 'Error al iniciar sesión'}, status=500)


@csrf_exempt
def logout_view(request):
    """Endpoint para cerrar sesión. Elimina el token."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

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

    user = get_user_from_token(request)
    if not user:
        return JsonResponse({'error': 'Token inválido o no proporcionado'}, status=401)

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


@csrf_exempt
def registro_view(request):
    """
    Endpoint para registrar nuevo docente.

    ⚠️ ATENCIÓN: este endpoint permite crear cuentas sin autenticación.
    En ARIA los docentes los crea el administrador desde el panel de Django.
    Si esta vista está ruteada en auth_urls.py, cualquiera puede registrarse.
    Verificá las urls y sacala si no la usás.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        from apps.docentes.models import Docente as DocenteModel, Institucion

        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        institucion_id = data.get('institucion_id')

        if not email or not password:
            return JsonResponse({'error': 'Email y contraseña son requeridos'}, status=400)

        if DocenteModel.objects.filter(email__iexact=email).exists():
            return JsonResponse({'error': 'Ya existe un docente con ese email'}, status=400)

        institucion = None
        if institucion_id:
            try:
                institucion = Institucion.objects.get(id=institucion_id)
            except Institucion.DoesNotExist:
                pass

        docente = DocenteModel.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            institucion=institucion,
        )

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
        logger.error(f"Error en registro: {e}", exc_info=True)
        return JsonResponse({'error': 'Error al crear la cuenta'}, status=500)


@csrf_exempt
def cambiar_password_view(request):
    """
    Cambio de contraseña del docente autenticado.
    Requiere la contraseña actual (el docente ya está adentro).
    """
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
            return JsonResponse(
                {'error': 'Contraseña actual y nueva son requeridas'}, status=400
            )

        if not user.check_password(password_actual):
            return JsonResponse({'error': 'La contraseña actual es incorrecta'}, status=400)

        # Usa los AUTH_PASSWORD_VALIDATORS configurados en settings
        try:
            validate_password(password_nuevo, user)
        except ValidationError as e:
            return JsonResponse({'error': ' '.join(e.messages)}, status=400)

        user.set_password(password_nuevo)
        user.save()

        # Renovar token: invalida las sesiones abiertas en otros dispositivos
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        logger.info(f"Contraseña cambiada por el docente {user.pk}")

        return JsonResponse({
            'success': True,
            'message': 'Contraseña cambiada correctamente',
            'token': token.key
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error cambiando contraseña del docente {user.pk}: {e}", exc_info=True)
        return JsonResponse({'error': 'Error al cambiar la contraseña'}, status=500)


# =============================================================================
# RECUPERACIÓN DE CONTRASEÑA (público, sin autenticación)
# =============================================================================

class ResetPasswordThrottle(ScopedRateThrottle):
    """Limita los intentos por IP. Endpoint público que dispara envío de mails."""
    scope = 'reset_password'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ResetPasswordThrottle])
def solicitar_reset_password(request):
    """
    Paso 1: el docente ingresa su mail y se le envía un enlace de recuperación.

    La respuesta es siempre idéntica, exista o no el mail en la base.
    Si variara, cualquiera podría averiguar qué direcciones están registradas.
    """
    email = (request.data.get('email') or '').strip().lower()

    respuesta = Response(
        {
            'success': True,
            'message': 'Si el correo está registrado, vas a recibir un enlace.'
        },
        status=status.HTTP_200_OK
    )

    if not email:
        return respuesta

    docente = Docente.objects.filter(email__iexact=email, is_active=True).first()
    if not docente:
        logger.info("Reset de contraseña solicitado para un mail no registrado")
        return respuesta

    uid = urlsafe_base64_encode(force_bytes(docente.pk))
    token = default_token_generator.make_token(docente)
    link = f"{settings.FRONTEND_URL}/restablecer/{uid}/{token}"

    cuerpo = (
        f"Hola {docente.first_name or 'docente'},\n\n"
        f"Recibimos un pedido para restablecer tu contraseña de ARIA.\n\n"
        f"Entrá acá para crear una nueva:\n{link}\n\n"
        f"El enlace vence en una hora y sirve una sola vez.\n"
        f"Si no pediste esto, ignorá el mensaje: tu contraseña sigue igual.\n\n"
        f"ARIA — Escuela Municipal Dr. Jorge Orgaz"
    )

    try:
        send_mail(
            subject='Restablecer tu contraseña de ARIA',
            message=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[docente.email],
            fail_silently=False,
        )
        logger.info(f"Mail de reset enviado al docente {docente.pk}")
    except Exception as e:
        logger.error(f"Error enviando mail de reset al docente {docente.pk}: {e}", exc_info=True)

    return respuesta


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ResetPasswordThrottle])
def confirmar_reset_password(request):
    """
    Paso 2: con el uid y el token del enlace, el docente define su contraseña nueva.

    El token de Django se deriva del hash de la contraseña y del last_login,
    así que se invalida solo en cuanto la contraseña cambia. No hay que
    guardarlo ni limpiarlo.
    """
    uid = request.data.get('uid')
    token = request.data.get('token')
    password_nuevo = request.data.get('password_nuevo') or ''

    try:
        docente_pk = force_str(urlsafe_base64_decode(uid))
        docente = Docente.objects.get(pk=docente_pk, is_active=True)
    except Exception:
        return Response(
            {'error': 'El enlace no es válido.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not default_token_generator.check_token(docente, token):
        return Response(
            {'error': 'El enlace venció o ya se usó. Pedí uno nuevo.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        validate_password(password_nuevo, docente)
    except ValidationError as e:
        return Response({'error': ' '.join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    docente.set_password(password_nuevo)
    docente.save()

    # Cierra las sesiones abiertas en otros dispositivos
    Token.objects.filter(user=docente).delete()

    logger.info(f"Contraseña restablecida para el docente {docente.pk}")

    return Response({
        'success': True,
        'message': 'Contraseña actualizada correctamente.'
    })


# =============================================================================
# AUXILIARES
# =============================================================================

def get_user_from_token(request):
    """
    Obtiene el usuario a partir del header Authorization.
    Útil para las vistas planas de Django que no pasan por DRF.
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Token '):
        return None

    partes = auth_header.split(' ')
    if len(partes) < 2 or not partes[1]:
        return None

    try:
        token = Token.objects.get(key=partes[1])
        return token.user
    except Token.DoesNotExist:
        return None