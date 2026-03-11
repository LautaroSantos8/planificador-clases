from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/ai/', include('apps.ai.urls')),
    path('api/auth/', include('apps.docentes.auth_urls')),
    path('api/docentes/', include('apps.docentes.urls')),
    path('api/planificacion/', include('apps.planificacion.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)