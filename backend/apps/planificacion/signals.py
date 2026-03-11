from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import NivelAlumno, HistorialNivel


@receiver(pre_save, sender=NivelAlumno)
def registrar_cambio_nivel(sender, instance, **kwargs):
    """Guarda historial automáticamente cuando cambia el nivel de un alumno"""
    if instance.pk:
        try:
            anterior = NivelAlumno.objects.get(pk=instance.pk)
            if anterior.nivel != instance.nivel:
                HistorialNivel.objects.create(
                    nivel_alumno=instance,
                    nivel_anterior=anterior.nivel,
                    nivel_nuevo=instance.nivel,
                    motivo=getattr(instance, '_motivo_cambio', '')
                )
        except NivelAlumno.DoesNotExist:
            pass