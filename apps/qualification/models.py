from django.db import models

from apps.core.models import TimeStampedModel, UserTrackedModel
from apps.core.utils import navdata_next_due


class QualificationCycle(UserTrackedModel):
    class Kind(models.TextChoices):
        QTG = "qtg", "QTG Validation"
        SUBJECTIVE = "subjective", "Subjective Tests"

    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="cycles",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    last_completed = models.DateField(null=True, blank=True)
    next_due = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["device", "kind"], name="uniq_device_cycle_kind"),
        ]
        ordering = ["device__name", "kind"]

    def __str__(self):
        return f"{self.get_kind_display()} — {self.device}"


class QualificationEvent(TimeStampedModel):
    cycle = models.ForeignKey(
        QualificationCycle,
        on_delete=models.CASCADE,
        related_name="history",
    )
    date = models.DateField()
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.cycle} @ {self.date}"


class NavdataRecord(UserTrackedModel):
    device = models.OneToOneField(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="navdata",
    )
    last_updated = models.DateField(null=True, blank=True)
    cycle_ref = models.CharField(max_length=40, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Navdata — {self.device}"

    @property
    def next_due(self):
        return navdata_next_due(self.last_updated, self.device.navdata_cycle)


class NavdataEvent(TimeStampedModel):
    record = models.ForeignKey(
        NavdataRecord,
        on_delete=models.CASCADE,
        related_name="history",
    )
    date = models.DateField()
    cycle_ref = models.CharField(max_length=40, blank=True)
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.record} @ {self.date}"
