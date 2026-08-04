from pathlib import Path
from dotenv import load_dotenv
import os
import sys

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.getenv('DEBUG', 'False') == 'True'

# En producción la SECRET_KEY es obligatoria: si falta, el proceso no arranca.
# Arrancar con la clave de desarrollo sin que nadie se entere es peor que fallar.
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-key-solo-para-desarrollo'
    else:
        raise RuntimeError('Falta la variable de entorno SECRET_KEY en producción.')

# ALLOWED_HOSTS: en producción se lee de la variable de entorno
_allowed = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]

# Railway agrega automáticamente la URL del servicio
ALLOWED_HOSTS += ['.railway.app', '.up.railway.app']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    # Local apps
    'apps.ai',
    'apps.docentes',
    'apps.planificacion',
    'apps.curricula',
]

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Cordoba'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
_cors = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors.split(',') if o.strip()]
CORS_ALLOW_CREDENTIALS = True

AUTH_USER_MODEL = 'docentes.Docente'

# ============================================================
# RUTAS DE DATOS
# ============================================================
DATA_DIR = BASE_DIR / 'data'
CURRICULA_DIR = BASE_DIR / 'curricula'
CHROMA_DIR = DATA_DIR / 'chroma'

# El volumen de Railway puede montarse vacío: crear los directorios al arrancar
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# BASE DE DATOS
# ============================================================
# WAL permite lecturas concurrentes mientras hay una escritura en curso.
# Con 4 workers gthread (16 hilos) es la diferencia entre funcionar y
# devolver "database is locked" al docente.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATA_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
            'init_command': (
                'PRAGMA journal_mode=WAL;'
                'PRAGMA synchronous=NORMAL;'
                'PRAGMA busy_timeout=20000;'
            ),
            'transaction_mode': 'IMMEDIATE',
        },
    }
}

# ============================================================
# CACHÉ
# ============================================================
# DRF guarda los contadores de throttling acá. LocMemCache no sirve:
# es por proceso, así que con 4 workers el límite se multiplica por 4.
# DatabaseCache lo comparte entre workers y sobrevive los reinicios.
# Requiere: python manage.py createcachetable
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    }
}

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================
# El throttling se aplica por vista con @throttle_classes.
# Acá solo se declaran las tasas de cada scope.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'reset_password': '5/hour',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]

# ============================================================
# CORREO Y RECUPERACIÓN DE CONTRASEÑA
# ============================================================
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
PASSWORD_RESET_TIMEOUT = 3600  # el enlace vive 1 hora

# Railway bloquea SMTP en el plan Hobby, así que en producción
# se entrega por la API HTTP de Resend.
RESEND_API_KEY = os.getenv('RESEND_API_KEY')

if DEBUG:
    # En desarrollo el mail se imprime en la consola
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'utils.email_backend.ResendEmailBackend'

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'ARIA <noreply@aria.edu.ar>')

# ============================================================
# LOGGING
# ============================================================
# Sin esto, los logger.info/error de las apps no llegan a ningún lado:
# los loggers propagan a root, y root sin handlers descarta todo.
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO' if not DEBUG else 'DEBUG')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detallado': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'consola': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,   # Railway captura stdout
            'formatter': 'detallado',
        },
    },
    'root': {
        'handlers': ['consola'],
        'level': 'WARNING',
    },
    'loggers': {
        'apps': {
            'handlers': ['consola'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'utils': {
            'handlers': ['consola'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'django': {
            'handlers': ['consola'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['consola'],
            'level': 'WARNING',  # en DEBUG loguea cada query: demasiado ruido
            'propagate': False,
        },
    },
}

# ============================================================
# SEGURIDAD EN PRODUCCIÓN
# ============================================================
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'