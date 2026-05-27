from django.apps import AppConfig


class CoreReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.reports'
    label = 'reports'
    verbose_name = 'Reports Engine'
