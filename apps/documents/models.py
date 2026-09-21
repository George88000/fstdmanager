from django.db import models

from apps.core.models import TimeStampedModel, UserTrackedModel


class Folder(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    icon = models.CharField(max_length=16, default="📁")
    is_standard = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_standard", "name"]

    def __str__(self):
        return self.name


class Document(UserTrackedModel):
    legacy_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
    file = models.FileField(upload_to="documents/%Y/%m/", blank=True)
    original_name = models.CharField(max_length=255)
    mime = models.CharField(max_length=120, blank=True)
    size = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    uploaded_on = models.DateField(auto_now_add=True)
    folder = models.ForeignKey(
        Folder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents",
    )
    device = models.ForeignKey(
        "devices.Device",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents",
    )
    finding = models.ForeignKey(
        "findings.Finding",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="evidence_files",
    )
    maintenance_task = models.ForeignKey(
        "operations.MaintenanceTask",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    class Meta:
        ordering = ["-uploaded_on", "-id"]

    def __str__(self):
        return self.original_name
