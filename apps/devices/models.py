from django.db import models

from apps.core.models import UserTrackedModel
from apps.core.utils import minutes_to_hours_display


class Device(UserTrackedModel):
    class Type(models.TextChoices):
        FFS = "Full Flight Simulator (FFS)", "Full Flight Simulator (FFS)"
        FTD = "Flight Training Device (FTD)", "Flight Training Device (FTD)"
        FNPT = (
            "Flight and Navigation Procedures Trainer (FNPT)",
            "Flight and Navigation Procedures Trainer (FNPT)",
        )
        BITD = "Basic Instrument Trainer (BITD)", "Basic Instrument Trainer (BITD)"
        OTHER = "Other", "Other"

    class Level(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"
        I = "I", "I"
        II = "II", "II"
        III = "III", "III"

    class NavdataCycle(models.TextChoices):
        MONTHS_3 = "3m", "3 months"
        DAYS_28 = "28d", "28 days"

    class MaintenanceProgram(models.TextChoices):
        A = "program_a", "Monthly / 12-Month / 300-Hour / As Required"
        B = "program_b", "Monthly / 12-Month / As Required"
        C = "program_c", "Quarterly / Semester / 12-Month"

    legacy_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=80, choices=Type.choices, default=Type.FNPT)
    level = models.CharField(max_length=8, choices=Level.choices, blank=True)
    manufacturer = models.CharField(max_length=120, blank=True)
    serial = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    navdata_cycle = models.CharField(
        max_length=8,
        choices=NavdataCycle.choices,
        default=NavdataCycle.MONTHS_3,
    )
    maintenance_program = models.CharField(
        max_length=20,
        choices=MaintenanceProgram.choices,
        blank=True,
    )
    current_hours_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def current_hours_display(self):
        return minutes_to_hours_display(self.current_hours_minutes)
