from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserTrackedModel(TimeStampedModel):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated",
    )

    class Meta:
        abstract = True


class OrganizationSettings(models.Model):
    ato_name = models.CharField(max_length=200, default="FSTD Manager")
    threshold_days = models.PositiveSmallIntegerField(default=30)
    finding_categories = models.JSONField(default=list)

    class Meta:
        verbose_name = "Organization settings"
        verbose_name_plural = "Organization settings"

    def __str__(self):
        return self.ato_name

    @classmethod
    def get_solo(cls):
        from apps.core.constants import DEFAULT_FINDING_CATEGORIES

        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "ato_name": "FSTD Manager",
                "threshold_days": 30,
                "finding_categories": list(DEFAULT_FINDING_CATEGORIES),
            },
        )
        if not obj.finding_categories:
            obj.finding_categories = list(DEFAULT_FINDING_CATEGORIES)
            obj.save(update_fields=["finding_categories"])
        return obj
