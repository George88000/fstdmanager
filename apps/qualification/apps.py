from django.apps import AppConfig


class QualificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.qualification"
    label = "qualification"
    verbose_name = "Qualification"

    def ready(self):
        from apps.qualification import signals  # noqa: F401
