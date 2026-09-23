from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel, UserTrackedModel


class Folder(TimeStampedModel):
    name = models.CharField(max_length=80)
    icon = models.CharField(max_length=16, default="📁")
    is_standard = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )

    class Meta:
        ordering = ["-is_standard", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(parent__isnull=True),
                name="uniq_root_folder_name",
            ),
            models.UniqueConstraint(
                fields=["parent", "name"],
                condition=Q(parent__isnull=False),
                name="uniq_child_folder_name",
            ),
        ]

    def __str__(self):
        return self.name

    def ancestors(self):
        chain = []
        seen = set()
        current = self.parent
        while current is not None and current.pk not in seen:
            seen.add(current.pk)
            chain.append(current)
            current = current.parent
        chain.reverse()
        return chain

    def display_path(self):
        names = [folder.name for folder in self.ancestors()]
        names.append(self.name)
        return " / ".join(names)

    def colliding_child_names_on_delete(self):
        sibling_names = Folder.objects.filter(parent_id=self.parent_id).exclude(pk=self.pk).values_list(
            "name", flat=True
        )
        return list(self.children.filter(name__in=sibling_names).values_list("name", flat=True))

    def clean(self):
        if not self.parent_id or not self.pk:
            return
        if self.parent_id == self.pk:
            raise ValidationError({"parent": "A folder cannot be its own parent."})
        seen = set()
        current = self.parent
        while current is not None and current.pk not in seen:
            if current.pk == self.pk:
                raise ValidationError({"parent": "A folder cannot be nested under one of its descendants."})
            seen.add(current.pk)
            current = current.parent

    def delete(self, using=None, keep_parents=False):
        self.children.update(parent_id=self.parent_id)
        return super().delete(using=using, keep_parents=keep_parents)


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
