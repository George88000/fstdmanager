from django.db import models
from django.utils import timezone

from apps.core.constants import HIL_CATEGORIES
from apps.core.models import TimeStampedModel, UserTrackedModel
from apps.core.utils import add_days, minutes_to_hours_display, task_definition


class HoldItem(UserTrackedModel):
    class Version(models.TextChoices):
        MEP = "MEP", "MEP"
        SEP = "SEP", "SEP"
        BOTH = "BOTH", "BOTH"
        JET = "JET", "JET"

    class Category(models.TextChoices):
        MIN = "MIN", "Minor (90 days)"
        MAJ = "MAJ", "Major (30 days)"
        OBS = "OBS", "Observation (no limit)"

    legacy_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="hold_items",
    )
    seq = models.PositiveIntegerField()
    atl_log_item = models.CharField(max_length=80, blank=True)
    affected_version = models.CharField(max_length=8, choices=Version.choices, blank=True)
    description = models.TextField(blank=True)
    initials_report = models.CharField(max_length=80, blank=True)
    report_date = models.DateField(null=True, blank=True)
    defect_category = models.CharField(max_length=8, choices=Category.choices, blank=True)
    due_date = models.DateField(null=True, blank=True)
    closure_atl_log_item = models.CharField(max_length=80, blank=True)
    closure_hours = models.CharField(max_length=20, blank=True)
    closure_date = models.DateField(null=True, blank=True)
    initials_closure = models.CharField(max_length=80, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["device", "seq"], name="uniq_hil_device_seq"),
        ]
        ordering = ["device__name", "seq"]

    def __str__(self):
        return f"HIL {self.seq} — {self.device}"

    @property
    def is_open(self):
        return self.closure_date is None

    def save(self, *args, **kwargs):
        if not self.seq:
            last = (
                HoldItem.objects.filter(device=self.device)
                .order_by("-seq")
                .values_list("seq", flat=True)
                .first()
            )
            self.seq = (last or 0) + 1
        if not self.due_date and self.report_date and self.defect_category:
            days = HIL_CATEGORIES.get(self.defect_category, {}).get("days")
            if days:
                self.due_date = add_days(self.report_date, days)
        if self.closure_date:
            if not self.closed_at:
                self.closed_at = timezone.now()
        else:
            self.closed_at = None
            self.archived_at = None
        super().save(*args, **kwargs)


class PermanentDefect(UserTrackedModel):
    legacy_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="permanent_defects",
    )
    seq = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=80, blank=True)
    date_noted = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["device", "seq"], name="uniq_perm_device_seq"),
        ]
        ordering = ["device__name", "seq"]

    def __str__(self):
        return f"{self.title} — {self.device}"

    @property
    def ref(self):
        return f"PERM-{self.seq:04d}"

    def save(self, *args, **kwargs):
        if not self.seq:
            last = (
                PermanentDefect.objects.filter(device=self.device)
                .order_by("-seq")
                .values_list("seq", flat=True)
                .first()
            )
            self.seq = (last or 0) + 1
        super().save(*args, **kwargs)


class MaintenanceTask(UserTrackedModel):
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="maintenance_tasks",
    )
    task_key = models.CharField(max_length=40)
    last_completed = models.DateField(null=True, blank=True)
    next_due = models.DateField(null=True, blank=True)
    last_service_hours_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["device", "task_key"], name="uniq_device_task"),
        ]
        ordering = ["device__name", "task_key"]

    def __str__(self):
        return f"{self.task_name} — {self.device}"

    @property
    def definition(self):
        return task_definition(self.device.maintenance_program, self.task_key) or {
            "key": self.task_key,
            "name": self.task_key,
            "kind": "",
        }

    @property
    def task_name(self):
        return self.definition.get("name", self.task_key)

    @property
    def kind(self):
        return self.definition.get("kind", "")

    @property
    def last_service_hours_display(self):
        return minutes_to_hours_display(self.last_service_hours_minutes)


class MaintenanceEvent(TimeStampedModel):
    task = models.ForeignKey(
        MaintenanceTask,
        on_delete=models.CASCADE,
        related_name="history",
    )
    date = models.DateField()
    notes = models.CharField(max_length=500, blank=True)
    service_hours_minutes = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.task} @ {self.date}"
