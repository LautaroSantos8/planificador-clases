from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Institucion(models.Model):
    """Escuela o colegio"""
    PROVINCIA_CHOICES = [
        ('cordoba', 'Córdoba'),
        ('buenos_aires', 'Buenos Aires'),
        ('santa_fe', 'Santa Fe'),
        ('mendoza', 'Mendoza'),
        ('tucuman', 'Tucumán'),
        ('entre_rios', 'Entre Ríos'),
        ('salta', 'Salta'),
        ('misiones', 'Misiones'),
        ('chaco', 'Chaco'),
        ('corrientes', 'Corrientes'),
        ('santiago_del_estero', 'Santiago del Estero'),
        ('san_juan', 'San Juan'),
        ('jujuy', 'Jujuy'),
        ('rio_negro', 'Río Negro'),
        ('neuquen', 'Neuquén'),
        ('formosa', 'Formosa'),
        ('chubut', 'Chubut'),
        ('san_luis', 'San Luis'),
        ('catamarca', 'Catamarca'),
        ('la_rioja', 'La Rioja'),
        ('la_pampa', 'La Pampa'),
        ('santa_cruz', 'Santa Cruz'),
        ('tierra_del_fuego', 'Tierra del Fuego'),
        ('caba', 'Ciudad Autónoma de Buenos Aires'),
    ]

    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=300, blank=True)
    localidad = models.CharField(max_length=100, default='Córdoba')
    provincia = models.CharField(max_length=50, choices=PROVINCIA_CHOICES, default='cordoba')
    municipio = models.CharField(max_length=100, default='Córdoba Capital')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Instituciones"

    def __str__(self):
        return self.nombre


class Materia(models.Model):
    """Materias disponibles en una institución"""
    nombre = models.CharField(max_length=100)
    institucion = models.ForeignKey(Institucion, on_delete=models.CASCADE, related_name='materias')

    class Meta:
        verbose_name_plural = "Materias"
        unique_together = ['nombre', 'institucion']

    def __str__(self):
        return f"{self.nombre} - {self.institucion.nombre}"

class DocenteManager(BaseUserManager):
    """Manager personalizado para usar email como username."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        extra_fields.pop('username', None)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if email is None and 'username' in extra_fields:
            email = extra_fields.pop('username')
        return self.create_user(email, password, **extra_fields)

class Docente(AbstractUser):
    """Usuario docente del sistema"""
    institucion = models.ForeignKey(
        Institucion, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='docentes'
    )
    
    telefono = models.CharField(max_length=20, blank=True)
    
    objects = DocenteManager()
    
    class Meta:
        verbose_name_plural = "Docentes"
    
    def __str__(self):
        return f"{self.get_full_name() or self.username}"


class AsignacionDocente(models.Model):
    """Qué materia/grado/turno enseña cada docente"""
    TURNO_CHOICES = [
        ('M', 'Mañana'),
        ('T', 'Tarde'),
    ]
    GRADO_CHOICES = [
        (-2, 'Sala de 4 (Jardín)'),
        (-1, 'Sala de 5 (Jardín)'),
        (1, '1° Grado'),
        (2, '2° Grado'),
        (3, '3° Grado'),
        (4, '4° Grado'),
        (5, '5° Grado'),
        (6, '6° Grado'),
    ]
    DIVISION_CHOICES = [
        ('A', 'División A'),
        ('B', 'División B'),
        ('C', 'División C'),
        ('D', 'División D'),
    ]

    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='asignaciones')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='asignaciones')
    grado = models.IntegerField(choices=GRADO_CHOICES)
    turno = models.CharField(max_length=1, choices=TURNO_CHOICES)
    division = models.CharField(max_length=1, choices=DIVISION_CHOICES, default='A')

    class Meta:
        verbose_name_plural = "Asignaciones de Docentes"
        unique_together = ['docente', 'materia', 'grado', 'division', 'turno']

    def __str__(self):
        return f"{self.docente} - {self.materia.nombre} - {self.get_grado_display()} {self.get_turno_display()}"