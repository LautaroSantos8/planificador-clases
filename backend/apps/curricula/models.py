from django.db import models
from apps.docentes.models import Institucion


class DocumentoCurricula(models.Model):
    """
    Modelo unificado para todos los documentos curriculares.
    Soporta: NAP, Currículum Córdoba y Actualizaciones Municipales.
    """
    
    # Nivel del documento (prioridad de búsqueda)
    NIVEL_CHOICES = [
        ('nacional', 'Nacional (NAP)'),
        ('provincial', 'Provincial (Currículum Córdoba)'),
        ('municipal', 'Municipal (Actualizaciones)'),
    ]
    
    # Tipo de documento
    TIPO_CHOICES = [
        ('nap_ciclo', 'NAP por Ciclo'),
        ('mcc', 'Marco Curricular Común'),
        ('orientaciones', 'Orientaciones Pedagógicas y Didácticas'),
        ('progresiones', 'Progresiones de Aprendizaje'),
        ('actualizacion', 'Actualización Curricular'),
    ]
    
    # Ciclo educativo
    CICLO_CHOICES = [
        ('todos', 'Todos los ciclos'),
        ('primero', 'Primer Ciclo (1°, 2°, 3°)'),
        ('segundo', 'Segundo Ciclo (4°, 5°, 6°)'),
    ]
    
    # Materia (opcional, algunos documentos son generales)
    MATERIA_CHOICES = [
        ('todas', 'Todas las materias'),
        ('matematicas', 'Matemática'),
        ('lengua', 'Lengua y Literatura'),
        ('ciencias_naturales', 'Ciencias Naturales'),
        ('ciencias_sociales', 'Ciencias Sociales'),
    ]
    
    # Información básica
    titulo = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True)
    
    # Clasificación
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ciclo = models.CharField(max_length=20, choices=CICLO_CHOICES, default='todos')
    materia = models.CharField(max_length=30, choices=MATERIA_CHOICES, default='todas')
    
    # Para documentos provinciales (filtrar por provincia)
    provincia = models.CharField(
        max_length=50, 
        choices=Institucion.PROVINCIA_CHOICES, 
        blank=True,
        help_text="Solo para documentos provinciales"
    )
    
    # Para documentos municipales (filtrar por municipio)
    municipio = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Solo para actualizaciones municipales"
    )
    año_actualizacion = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Año de la actualización (ej: 2023)"
    )
    
    # Archivo
    archivo = models.FileField(upload_to='curricula/')
    
    # Estado de procesamiento para ChromaDB
    procesado = models.BooleanField(default=False)
    chunks_count = models.IntegerField(default=0, help_text="Fragmentos en ChromaDB")
    
    # Vigencia
    vigente = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documento Curricular"
        verbose_name_plural = "Documentos Curriculares"
        ordering = ['nivel', 'tipo', 'materia']

    def __str__(self):
        return f"[{self.get_nivel_display()}] {self.titulo}"
    
    def get_coleccion_chroma(self):
        """Devuelve el nombre de la colección de ChromaDB según el nivel."""
        if self.nivel == 'nacional':
            return 'curricula_nacional'
        elif self.nivel == 'provincial':
            return 'curricula_provincial'
        elif self.nivel == 'municipal':
            return 'actualizaciones_municipal'
        return 'curricula_nacional'