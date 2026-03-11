from django.contrib import admin
from .models import Alumno, NivelAlumno, ProyectoAula, PlanificacionGenerada


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ['apellido', 'nombre', 'grado', 'turno', 'institucion']
    list_filter = ['grado', 'turno', 'institucion']
    search_fields = ['nombre', 'apellido']


@admin.register(NivelAlumno)
class NivelAlumnoAdmin(admin.ModelAdmin):
    list_display = ['alumno', 'asignacion', 'nivel']
    list_filter = ['nivel', 'asignacion__materia']


@admin.register(ProyectoAula)
class ProyectoAulaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'asignacion', 'procesado', 'created_at']
    list_filter = ['procesado', 'asignacion__materia']


@admin.register(PlanificacionGenerada)
class PlanificacionGeneradaAdmin(admin.ModelAdmin):
    list_display = ['id', 'asignacion', 'fue_util', 'created_at']
    list_filter = ['fue_util', 'asignacion__materia']