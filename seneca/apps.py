from django.apps import AppConfig


class SenecaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seneca'

    def ready(self):
        import seneca.signals
