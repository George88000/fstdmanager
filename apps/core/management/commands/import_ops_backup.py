import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import OrganizationSettings
from apps.core.utils import hours_to_minutes, parse_date
from apps.devices.models import Device
from apps.documents.models import Folder
from apps.findings.models import Finding
from apps.operations.models import HoldItem, MaintenanceEvent, MaintenanceTask, PermanentDefect
from apps.qualification.models import (
    NavdataEvent,
    NavdataRecord,
    QualificationCycle,
    QualificationEvent,
)
from apps.remote.models import RemoteConnection


class Command(BaseCommand):
    help = "Import FSTD Ops Manager JSON backup (idempotent on legacy_id)."

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, help="Path to fstd-ops-backup.json")

    def handle(self, *args, **options):
        path = Path(options["json_path"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        with transaction.atomic():
            self._import_settings(data.get("settings") or {})
            devices = self._import_devices(data.get("devices") or [])
            self._import_cycles(devices, data.get("qtg") or [], QualificationCycle.Kind.QTG)
            self._import_cycles(devices, data.get("subjective") or [], QualificationCycle.Kind.SUBJECTIVE)
            self._import_navdata(devices, data.get("navdata") or [])
            self._import_findings(devices, data.get("findings") or [])
            self._import_hold_items(devices, data.get("holdItems") or [])
            self._import_permanent_defects(devices, data.get("permanentDefects") or [])
            self._import_maintenance(devices, data.get("maintenanceTasks") or [])
            self._import_folders(data.get("folders") or [])
            self._import_remote(devices, data.get("remoteConnections") or [])
        self.stdout.write(self.style.SUCCESS(f"Imported backup from {path}"))

    def _import_settings(self, payload):
        settings = OrganizationSettings.get_solo()
        settings.ato_name = payload.get("atoName") or settings.ato_name
        settings.threshold_days = payload.get("thresholdDays") or settings.threshold_days
        categories = payload.get("findingCategories")
        if categories:
            settings.finding_categories = categories
        settings.save()

    def _import_devices(self, rows):
        mapping = {}
        for row in rows:
            device, _ = Device.objects.update_or_create(
                legacy_id=row["id"],
                defaults={
                    "name": row.get("name") or "",
                    "type": row.get("type") or Device.Type.FNPT,
                    "level": row.get("level") or "",
                    "manufacturer": row.get("manufacturer") or "",
                    "serial": row.get("serial") or "",
                    "location": row.get("location") or "",
                    "notes": row.get("notes") or "",
                    "navdata_cycle": row.get("navdataCycle") or Device.NavdataCycle.MONTHS_3,
                    "maintenance_program": row.get("maintenanceProgram") or "",
                    "current_hours_minutes": hours_to_minutes(row.get("currentHours")) or 0,
                },
            )
            mapping[row["id"]] = device
        self.stdout.write(f"Devices: {len(mapping)}")
        return mapping

    def _import_cycles(self, devices, rows, kind):
        for row in rows:
            device = devices.get(row.get("deviceId"))
            if not device:
                continue
            cycle, _ = QualificationCycle.objects.update_or_create(
                device=device,
                kind=kind,
                defaults={
                    "last_completed": parse_date(row.get("lastCompleted")),
                    "next_due": parse_date(row.get("nextDue")),
                    "notes": row.get("notes") or "",
                },
            )
            for event in row.get("history") or []:
                date_value = parse_date(event.get("date"))
                if not date_value:
                    continue
                QualificationEvent.objects.get_or_create(
                    cycle=cycle,
                    date=date_value,
                    defaults={"notes": event.get("notes") or ""},
                )

    def _import_navdata(self, devices, rows):
        for row in rows:
            device = devices.get(row.get("deviceId"))
            if not device:
                continue
            record, _ = NavdataRecord.objects.update_or_create(
                device=device,
                defaults={
                    "last_updated": parse_date(row.get("lastUpdated")),
                    "cycle_ref": row.get("cycleRef") or "",
                    "notes": row.get("notes") or "",
                },
            )
            for event in row.get("history") or []:
                date_value = parse_date(event.get("date"))
                if not date_value:
                    continue
                NavdataEvent.objects.get_or_create(
                    record=record,
                    date=date_value,
                    defaults={
                        "cycle_ref": event.get("cycleRef") or "",
                        "notes": event.get("notes") or "",
                    },
                )

    def _import_findings(self, devices, rows):
        count = 0
        for row in rows:
            device = devices.get(row.get("deviceId")) if row.get("deviceId") else None
            Finding.objects.update_or_create(
                legacy_id=row["id"],
                defaults={
                    "source": row.get("source") or Finding.Source.AUTHORITY,
                    "seq": row.get("seq") or 1,
                    "title": row.get("title") or "",
                    "category": row.get("category") or "Other",
                    "cls": row.get("cls") or "",
                    "kind": row.get("kind") or "",
                    "device": device,
                    "authority": row.get("authority") or "",
                    "date_raised": parse_date(row.get("dateRaised")),
                    "due_date": parse_date(row.get("dueDate")),
                    "status": row.get("status") or Finding.Status.OPEN,
                    "description": row.get("description") or "",
                    "resolution": row.get("resolution") or "",
                    "closure_evidence": row.get("closureEvidence") or "",
                },
            )
            count += 1
        self.stdout.write(f"Findings: {count}")

    def _import_hold_items(self, devices, rows):
        count = 0
        for row in rows:
            device = devices.get(row.get("deviceId"))
            if not device:
                continue
            HoldItem.objects.update_or_create(
                legacy_id=row["id"],
                defaults={
                    "device": device,
                    "seq": row.get("seq") or 1,
                    "atl_log_item": row.get("atlLogItem") or "",
                    "affected_version": row.get("affectedVersion") or "",
                    "description": row.get("description") or "",
                    "initials_report": row.get("initialsReport") or "",
                    "report_date": parse_date(row.get("reportDate")),
                    "defect_category": row.get("defectCategory") or "",
                    "due_date": parse_date(row.get("dueDate")),
                    "closure_atl_log_item": row.get("closureAtlLogItem") or "",
                    "closure_hours": row.get("closureHours") or "",
                    "closure_date": parse_date(row.get("closureDate")),
                    "initials_closure": row.get("initialsClosure") or "",
                },
            )
            count += 1
        self.stdout.write(f"Hold items: {count}")

    def _import_permanent_defects(self, devices, rows):
        for row in rows:
            device = devices.get(row.get("deviceId"))
            if not device:
                continue
            PermanentDefect.objects.update_or_create(
                legacy_id=row["id"],
                defaults={
                    "device": device,
                    "seq": row.get("seq") or 1,
                    "title": row.get("title") or "",
                    "category": row.get("category") or "",
                    "date_noted": parse_date(row.get("dateNoted")),
                    "reference": row.get("reference") or "",
                    "description": row.get("description") or "",
                },
            )

    def _import_maintenance(self, devices, rows):
        for row in rows:
            device = devices.get(row.get("deviceId"))
            if not device:
                continue
            task, _ = MaintenanceTask.objects.update_or_create(
                device=device,
                task_key=row.get("taskKey") or "",
                defaults={
                    "last_completed": parse_date(row.get("lastCompleted")),
                    "next_due": parse_date(row.get("nextDue")),
                    "last_service_hours_minutes": hours_to_minutes(row.get("lastServiceHours")),
                    "notes": row.get("notes") or "",
                },
            )
            for event in row.get("history") or []:
                date_value = parse_date(event.get("date"))
                if not date_value:
                    continue
                MaintenanceEvent.objects.get_or_create(
                    task=task,
                    date=date_value,
                    defaults={"notes": event.get("notes") or ""},
                )

    def _import_folders(self, rows):
        for row in rows:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            Folder.objects.get_or_create(
                name=name,
                defaults={
                    "icon": row.get("icon") or "📁",
                    "is_standard": bool(row.get("standard")),
                },
            )

    def _import_remote(self, devices, rows):
        for row in rows:
            connection, _ = RemoteConnection.objects.update_or_create(
                anydesk_id=row.get("anydeskCode") or row.get("anydesk_id") or "",
                defaults={
                    "label": row.get("label") or "",
                    "password": row.get("password") or "",
                    "notes": row.get("notes") or "",
                },
            )
            linked = [devices[did] for did in (row.get("deviceIds") or []) if did in devices]
            if linked:
                connection.devices.set(linked)
