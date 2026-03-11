from django.contrib import admin
from .models import DocumentoCurricula


@admin.register(DocumentoCurricula)
class DocumentoCurriculaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'nivel', 'tipo', 'materia', 'ciclo', 'procesado', 'vigente']
    list_filter = ['nivel', 'tipo', 'materia', 'ciclo', 'procesado', 'vigente', 'provincia']
    search_fields = ['titulo', 'descripcion']
    readonly_fields = ['procesado', 'chunks_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información del Documento', {
            'fields': ('titulo', 'descripcion', 'archivo')
        }),
        ('Clasificación', {
            'fields': ('nivel', 'tipo', 'ciclo', 'materia')
        }),
        ('Ubicación (solo si aplica)', {
            'fields': ('provincia', 'municipio', 'año_actualizacion'),
            'classes': ('collapse',),
            'description': 'Completar solo para documentos provinciales o municipales'
        }),
        ('Estado', {
            'fields': ('vigente', 'procesado', 'chunks_count'),
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ayuda contextual
        form.base_fields['nivel'].help_text = 'Nacional=NAP, Provincial=Currículum Córdoba, Municipal=Actualizaciones'
        return form