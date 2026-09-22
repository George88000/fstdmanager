from datetime import datetime, timezone as dt_timezone

from django.db import migrations
from django.utils import timezone


MIGRATION_TS = datetime(2026, 9, 22, 9, 0, tzinfo=dt_timezone.utc)
MIGRATION_DATE = MIGRATION_TS.date()


def backfill_closed_at(apps, schema_editor):
    Finding = apps.get_model("findings", "Finding")
    for finding in Finding.objects.filter(status="Closed", closed_at__isnull=True):
        if finding.updated_at and timezone.localdate(finding.updated_at) == MIGRATION_DATE:
            finding.closed_at = MIGRATION_TS
        else:
            finding.closed_at = finding.updated_at
        finding.save(update_fields=["closed_at"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("findings", "0003_add_archive_fields"),
    ]

    operations = [
        migrations.RunPython(backfill_closed_at, noop),
    ]
