from django.urls import path
from . import views

urlpatterns = [
    path('consultar/', views.consultar_asistente, name='consultar'),
    path('bienvenida/', views.mensaje_bienvenida, name='bienvenida'),
    path('estadisticas/', views.estadisticas_rag, name='estadisticas'),
    path('health/', views.health_check, name='health'),
    path('buscar-curricula/', views.buscar_curricula, name='buscar_curricula'),
    path('historial/', views.obtener_historial, name='historial'),
    path('feedback/', views.guardar_feedback, name='feedback'),
    path('exportar/', views.exportar_planificacion, name='exportar'),
]
