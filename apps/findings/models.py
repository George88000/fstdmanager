from django.db import models

from apps.core.models import UserTrackedModel


class Finding(UserTrackedModel):
    class Source(models.TextChoices):
        AUTHORITY = "authority", "Authority"
        INTERNAL = "internal", "Internal audit"

    class Status(models.TextChoices):
        OPEN = "Open", "Open"
        IN_PROGRESS = "In Progress", "In Progress"
        AWAITING = "Awaiting Authority", "Awaiting Authority"
        CLOSED = "Closed", "Closed"

    class Kind(models.TextChoices):
        SUBJECTIVE = "Subjective", "Subjective"
        OBJECTIVE = "Objective", "Objective"

    class Cls(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"
        E = "E", "E"

    legacy_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices)
    seq = models.PositiveIntegerField()
    title = models.CharField(max_length=500)
    category = models.CharField(max_length=80)
    cls = models.CharField(max_length=1, choices=Cls.choices, blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, blank=True)
    device = models.ForeignKey(
        "devices.Device",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="findings",
    )
    authority = models.CharField(max_length=120, blank=True)
    date_raised = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)
    description = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    closure_evidence = models.TextField(blank=True)

    class Meta:
        ordering = ["source", "seq", "id"]

    def __str__(self):
        prefix = "AUD" if self.source == self.Source.INTERNAL else "FIND"
        return f"{prefix}-{self.seq:04d} — {self.title}"

    @property
    def ref(self):
        prefix = "AUD" if self.source == self.Source.INTERNAL else "FIND"
        return f"{prefix}-{self.seq:04d}"

    def save(self, *args, **kwargs):
        if not self.seq:
            last = (
                Finding.objects.filter(source=self.source)
                .order_by("-seq")
                .values_list("seq", flat=True)
                .first()
            )
            self.seq = (last or 0) + 1
        super().save(*args, **kwargs)
