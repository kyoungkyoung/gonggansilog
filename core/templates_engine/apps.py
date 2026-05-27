from django.apps import AppConfig


class CoreTemplatesEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.templates_engine'
    label = 'templates_engine'  # Custom label for Django model references
    verbose_name = 'Templates Engine'
