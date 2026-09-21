from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.constants import MAINTENANCE_PROGRAMS
from apps.devices.models import Device
from apps.operations.models import MaintenanceTask


@receiver(post_save, sender=Device)
def ensure_maintenance_tasks(sender, instance, **kwargs):
    definitions = MAINTENANCE_PROGRAMS.get(instance.maintenance_program) or []
    for item in definitions:
        MaintenanceTask.objects.get_or_create(device=instance, task_key=item["key"])
