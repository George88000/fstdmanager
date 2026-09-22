from datetime import datetime, time, timezone as dt_timezone

from django.db import migrations
from django.utils import timezone


MIGRATION_TS = datetime(2026, 9, 22, 9, 0, tzinfo=dt_timezone.utc)
MIGRATION_DATE = MIGRATION_TS.date()


def backfill_closed_at(apps, schema_editor):
    HoldItem = apps.get_model("operations", "HoldItem")
    for item in HoldItem.objects.filter(closure_date__isnull=False, closed_at__isnull=True):
        if item.closure_date == MIGRATION_DATE:
            item.closed_at = MIGRATION_TS
        else:
            item.closed_at = timezone.make_aware(
                datetime.combine(item.closure_date, time(9, 0)),
                timezone=dt_timezone.utc,
            )
        item.save(update_fields=["closed_at"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0002_add_archive_fields"),
    ]

    operations = [
        migrations.RunPython(backfill_closed_at, noop),
    ]
