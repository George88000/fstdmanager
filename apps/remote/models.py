from django.db import models

from apps.core.models import UserTrackedModel


class RemoteConnection(UserTrackedModel):
    label = models.CharField(max_length=120)
    anydesk_id = models.CharField(max_length=40)
    password = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    devices = models.ManyToManyField(
        "devices.Device",
        blank=True,
        related_name="remote_connections",
    )

    class Meta:
        ordering = ["label"]

    def __str__(self):
        return self.label
