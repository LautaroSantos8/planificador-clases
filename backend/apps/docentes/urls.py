from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    # Asignaciones
    path('asignaciones/', views.asignaciones, name='asignaciones'),
    path('asignaciones/<int:asignacion_id>/', views.eliminar_asignacion, name='eliminar_asignacion'),
    path('materias/', views.materias_disponibles, name='materias'),
]
