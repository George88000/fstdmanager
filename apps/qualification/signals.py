from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.devices.models import Device
from apps.qualification.models import NavdataRecord, QualificationCycle


@receiver(post_save, sender=Device)
def ensure_qualification_records(sender, instance, **kwargs):
    for kind in QualificationCycle.Kind.values:
        QualificationCycle.objects.get_or_create(device=instance, kind=kind)
    NavdataRecord.objects.get_or_create(device=instance)
