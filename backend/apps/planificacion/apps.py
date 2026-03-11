from django.apps import AppConfig


class PlanificacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.planificacion'

    def ready(self):
        import apps.planificacion.signals