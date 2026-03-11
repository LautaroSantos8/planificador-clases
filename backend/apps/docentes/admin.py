from django.contrib import admin
from .models import Institucion, Materia, Docente, AsignacionDocente


@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'localidad', 'created_at']
    search_fields = ['nombre', 'codigo']


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'institucion']
    list_filter = ['institucion']


@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'institucion', 'is_active']
    list_filter = ['institucion', 'is_active']
    search_fields = ['username', 'first_name', 'last_name']


@admin.register(AsignacionDocente)
class AsignacionDocenteAdmin(admin.ModelAdmin):
    list_display = ['docente', 'materia', 'grado', 'turno']
    list_filter = ['grado', 'turno', 'materia']