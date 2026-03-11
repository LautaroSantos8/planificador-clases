from django.db import models
from apps.docentes.models import Institucion, AsignacionDocente


class Alumno(models.Model):
    """Alumno de una institución"""
    TURNO_CHOICES = [
        ('M', 'Mañana'),
        ('T', 'Tarde'),
    ]
    GRADO_CHOICES = [
        (1, '1° Grado'),
        (2, '2° Grado'),
        (3, '3° Grado'),
        (4, '4° Grado'),
        (5, '5° Grado'),
        (6, '6° Grado'),
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE, related_name='alumnos')
    grado = models.IntegerField(choices=GRADO_CHOICES)
    turno = models.CharField(max_length=1, choices=TURNO_CHOICES)
    division = models.CharField(max_length=1, choices=AsignacionDocente.DIVISION_CHOICES, default='A')
    # Nota contextual general (opcional)
    observaciones = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Alumnos"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.apellido}, {self.nombre} - {self.get_grado_display()}"


class NivelAlumno(models.Model):
    """Nivel de desempeño de un alumno en una materia específica"""
    NIVEL_CHOICES = [
        ('NEE', 'Rezago Significativo'),  # 2+ grados por debajo
        ('LP', 'Logros en Proceso'),            # 1 grado por debajo
        ('LE', 'Logros Esperados'),               # Acorde al grado
    ]

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='niveles')
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE, related_name='niveles_alumnos')
    nivel = models.CharField(max_length=4, choices=NIVEL_CHOICES, default='LE')
    
    # Nota contextual específica para esta materia
    nota_contextual = models.TextField(blank=True, help_text="Ej: No tiene lectoescritura consolidada")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Niveles de Alumnos"
        unique_together = ['alumno', 'asignacion']  # Un nivel por alumno por asignación

    def __str__(self):
        return f"{self.alumno} - {self.asignacion.materia.nombre}: {self.get_nivel_display()}"


class DocumentoDocente(models.Model):
    """Documento subido por un docente (proyecto áulico o planificación anual)"""
    TIPO_CHOICES = [
        ('proyecto', 'Proyecto Áulico'),
        ('planificacion_anual', 'Planificación Anual'),
    ]

    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE, related_name='documentos')
    
    # Archivo subido
    archivo = models.FileField(upload_to='documentos_docentes/')
    
    # Contenido extraído para RAG
    contenido = models.TextField(blank=True, help_text="Contenido en texto extraído del archivo")
    
    # Estado de procesamiento
    procesado = models.BooleanField(default=False)
    chunks_generados = models.IntegerField(default=0)
    error_procesamiento = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documento Docente"
        verbose_name_plural = "Documentos Docentes"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo} - {self.asignacion}"


# Mantener ProyectoAula por compatibilidad (deprecated)
class ProyectoAula(models.Model):
    """DEPRECATED: Usar DocumentoDocente. Proyecto de aula subido por un docente"""
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE, related_name='proyectos')
    
    contenido = models.TextField(blank=True, help_text="Contenido en texto del proyecto")
    archivo = models.FileField(upload_to='proyectos/', blank=True, null=True)
    
    procesado = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Proyectos de Aula (Deprecado)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.titulo} - {self.asignacion}"


class PlanificacionGenerada(models.Model):
    """Registro de planificaciones generadas por la IA"""
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE, related_name='planificaciones')
    
    # Consulta del docente
    prompt_original = models.TextField()
    
    # Respuesta de la IA
    respuesta_ia = models.TextField()
    
    # Actividades diferenciadas generadas (JSON)
    actividades_json = models.JSONField(default=dict, blank=True)
    
    # Feedback del docente
    fue_util = models.BooleanField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Planificaciones Generadas"
        ordering = ['-created_at']

    def __str__(self):
        return f"Planificación {self.id} - {self.asignacion} - {self.created_at.strftime('%d/%m/%Y')}"


class HistorialNivel(models.Model):
    """Registro histórico de cambios de nivel de un alumno"""
    nivel_alumno = models.ForeignKey(NivelAlumno, on_delete=models.CASCADE, related_name='historial')
    nivel_anterior = models.CharField(max_length=4, choices=NivelAlumno.NIVEL_CHOICES)
    nivel_nuevo = models.CharField(max_length=4, choices=NivelAlumno.NIVEL_CHOICES)
    motivo = models.TextField(blank=True, help_text="Razón del cambio de nivel")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Historial de Niveles"
        ordering = ['-fecha']
