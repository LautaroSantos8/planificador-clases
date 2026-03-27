from django.urls import path
from . import views

urlpatterns = [
    # Alumnos
    path('alumnos/', views.alumnos_por_grado_division, name='alumnos_por_grado'),
    path('alumnos/observaciones/', views.actualizar_observaciones, name='actualizar_observaciones'),
    path('niveles/', views.niveles_por_alumno, name='niveles_por_alumno'),
    path('niveles/actualizar/', views.actualizar_nivel_alumno, name='actualizar_nivel'),
    # Documentos
    path('documentos/', views.documentos, name='documentos'),
    path('documentos/analizar/', views.analizar_documento, name='analizar_documento'),
    path('documentos/<int:documento_id>/', views.eliminar_documento, name='eliminar_documento'),
    # Estadísticas
    path('estadisticas/', views.estadisticas_docente, name='estadisticas_docente'),
]