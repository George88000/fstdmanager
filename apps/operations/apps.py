from django.apps import AppConfig


class OperationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.operations"
    label = "operations"
    verbose_name = "Operations"

    def ready(self):
        from apps.operations import signals  # noqa: F401
