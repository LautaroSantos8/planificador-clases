from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Institucion, Materia, Docente, AsignacionDocente

class DocenteCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Docente
        fields = ('username', 'email', 'first_name', 'last_name', 'institucion')

class DocenteChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Docente

@admin.register(Docente)
class DocenteAdmin(UserAdmin):
    add_form = DocenteCreationForm
    form = DocenteChangeForm
    model = Docente
    list_display = ['username', 'first_name', 'last_name', 'institucion', 'is_active']
    list_filter = ['institucion', 'is_active']
    search_fields = ['username', 'first_name', 'last_name']
    fieldsets = UserAdmin.fieldsets + (
        ('Institución', {'fields': ('institucion',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'institucion', 'password1', 'password2'),
        }),
    )

@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'localidad', 'created_at']
    search_fields = ['nombre', 'codigo']

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'institucion']
    list_filter = ['institucion']

@admin.register(AsignacionDocente)
class AsignacionDocenteAdmin(admin.ModelAdmin):
    list_display = ['docente', 'materia', 'grado', 'turno']
    list_filter = ['grado', 'turno', 'materia']