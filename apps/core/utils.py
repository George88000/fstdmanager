from __future__ import annotations

from calendar import monthrange
from collections import Counter
from datetime import date, timedelta
from typing import Any, Optional


def hours_to_minutes(value) -> Optional[int]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(round(float(value) * 60))
    text = str(value).strip()
    if not text:
        return None
    if ":" in text:
        hours, minutes = text.split(":", 1)
        return int(hours) * 60 + int(minutes)
    return int(round(float(text) * 60))


def minutes_to_hours_display(minutes: Optional[int]) -> str:
    if minutes is None:
        return ""
    hours, mins = divmod(int(minutes), 60)
    return f"{hours}:{mins:02d}"


def add_months(start: date, months: int) -> date:
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return date(year, month, day)


def add_days(start: Optional[date], days: int) -> Optional[date]:
    if start is None:
        return None
    return start + timedelta(days=days)


def days_until(due: Optional[date], today: Optional[date] = None) -> Optional[int]:
    if due is None:
        return None
    today = today or date.today()
    return (due - today).days


def status_from_due(due: Optional[date], threshold_days: int = 30) -> str:
    remaining = days_until(due)
    if remaining is None:
        return "none"
    if remaining < 0:
        return "over"
    if remaining <= threshold_days:
        return "soon"
    return "ok"


def parse_date(value) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def navdata_next_due(last_updated: Optional[date], cycle: str) -> Optional[date]:
    if last_updated is None:
        return None
    if cycle == "28d":
        return add_days(last_updated, 28)
    return add_months(last_updated, 3)


def maintenance_due_date(kind: str, last_completed: Optional[date]) -> Optional[date]:
    if last_completed is None:
        return None
    if kind == "monthly":
        return add_months(last_completed, 1)
    if kind == "annual":
        return add_months(last_completed, 12)
    if kind in {"quarterly_fixed", "semester_fixed"}:
        return None
    return None


def task_definition(program_key: str, task_key: str) -> Optional[dict]:
    from apps.core.constants import MAINTENANCE_PROGRAMS

    for item in MAINTENANCE_PROGRAMS.get(program_key, []):
        if item["key"] == task_key:
            return item
    return None


def maintenance_task_status(task, threshold_days: int = 30, hours_soon: int = 20) -> str:
    """Equivalent of maintStatus() in the HTML prototype."""
    definition = task.definition if hasattr(task, "definition") else {}
    kind = definition.get("kind", "")
    if kind == "as_required":
        return "none"
    if kind == "hours":
        interval = definition.get("hours_interval")
        base = task.last_service_hours_minutes
        current = task.device.current_hours_minutes or 0
        if interval is None or base is None:
            return "none"
        remaining_hours = (base + interval * 60 - current) / 60
        if remaining_hours <= 0:
            return "over"
        if remaining_hours <= hours_soon:
            return "soon"
        return "ok"
    return status_from_due(task.next_due, threshold_days)


def is_compliance_alert_status(status: str) -> bool:
    return status in {"over", "soon"}


def compliance_sort_key(due: Optional[date]) -> int:
    remaining = days_until(due)
    return remaining if remaining is not None else 9999


def build_compliance_alerts(threshold_days: int = 30) -> list[dict[str, Any]]:
    """Build unified upcoming/overdue compliance list (HTML prototype renderDashboard)."""
    from apps.devices.models import Device
    from apps.findings.models import Finding
    from apps.operations.models import HoldItem, MaintenanceTask
    from apps.qualification.models import QualificationCycle

    items: list[dict[str, Any]] = []

    qtg = QualificationCycle.objects.filter(kind=QualificationCycle.Kind.QTG).select_related("device")
    for row in qtg:
        status = status_from_due(row.next_due, threshold_days)
        if is_compliance_alert_status(status):
            items.append(
                {
                    "type": "QTG",
                    "label": "",
                    "device_name": row.device.name,
                    "due": row.next_due,
                    "status": status,
                    "url_name": "qualification:qtg",
                }
            )

    subjective = QualificationCycle.objects.filter(
        kind=QualificationCycle.Kind.SUBJECTIVE
    ).select_related("device")
    for row in subjective:
        status = status_from_due(row.next_due, threshold_days)
        if is_compliance_alert_status(status):
            items.append(
                {
                    "type": "Subjective test",
                    "label": "",
                    "device_name": row.device.name,
                    "due": row.next_due,
                    "status": status,
                    "url_name": "qualification:subjective",
                }
            )

    for device in Device.objects.select_related("navdata").all():
        record = getattr(device, "navdata", None)
        due = getattr(record, "next_due", None) if record else None
        status = status_from_due(due, threshold_days)
        if is_compliance_alert_status(status):
            items.append(
                {
                    "type": "Navdata",
                    "label": "",
                    "device_name": device.name,
                    "due": due,
                    "status": status,
                    "url_name": "qualification:navdata",
                }
            )

    for task in MaintenanceTask.objects.select_related("device"):
        status = maintenance_task_status(task, threshold_days)
        if is_compliance_alert_status(status):
            items.append(
                {
                    "type": f"Maintenance: {task.task_name}",
                    "label": "",
                    "device_name": task.device.name,
                    "due": task.next_due,
                    "status": status,
                    "url_name": "operations:maintenance",
                }
            )

    open_hil = HoldItem.objects.filter(closure_date__isnull=True).select_related("device")
    for hil in open_hil:
        status = status_from_due(hil.due_date, threshold_days)
        if is_compliance_alert_status(status):
            items.append(
                {
                    "type": f"Hold item (Item {hil.seq})",
                    "label": "",
                    "device_name": hil.device.name,
                    "due": hil.due_date,
                    "status": status,
                    "url_name": "operations:hold_items",
                }
            )

    open_findings = Finding.objects.filter(
        status__in=[
            Finding.Status.OPEN,
            Finding.Status.IN_PROGRESS,
            Finding.Status.AWAITING,
        ]
    ).select_related("device")
    for finding in open_findings:
        if not finding.due_date:
            continue
        status = status_from_due(finding.due_date, threshold_days)
        if not is_compliance_alert_status(status):
            continue
        prefix = (
            "Internal audit finding: "
            if finding.source == Finding.Source.INTERNAL
            else "Authority finding: "
        )
        items.append(
            {
                "type": f"{prefix}{finding.category}",
                "label": finding.title,
                "device_name": finding.device.name if finding.device else "General",
                "due": finding.due_date,
                "status": status,
                "url_name": (
                    "findings:internal"
                    if finding.source == Finding.Source.INTERNAL
                    else "findings:authority"
                ),
            }
        )

    items.sort(key=lambda item: compliance_sort_key(item["due"]))
    return items


def compliance_badge(items: list[dict[str, Any]]) -> dict[str, str]:
    if not items:
        return {"count": 0, "color": "green", "bg": "emerald"}
    if any(item["status"] == "over" for item in items):
        return {"count": len(items), "color": "red", "bg": "red"}
    return {"count": len(items), "color": "amber", "bg": "amber"}


def _stat_card(value: int, label: str, tone: str = "") -> dict[str, Any]:
    return {"value": value, "label": label, "tone": tone}


def dashboard_stat_cards(threshold_days: int = 30) -> list[dict[str, Any]]:
    from apps.devices.models import Device
    from apps.documents.models import Document
    from apps.findings.models import Finding
    from apps.operations.models import HoldItem, MaintenanceTask
    from apps.qualification.models import QualificationCycle

    devices = Device.objects.all()
    open_authority = Finding.objects.filter(source=Finding.Source.AUTHORITY).exclude(
        status=Finding.Status.CLOSED
    )
    open_internal = Finding.objects.filter(source=Finding.Source.INTERNAL).exclude(
        status=Finding.Status.CLOSED
    )
    open_hil = HoldItem.objects.filter(closure_date__isnull=True)

    qtg_alerts = sum(
        1
        for row in QualificationCycle.objects.filter(kind=QualificationCycle.Kind.QTG)
        if is_compliance_alert_status(status_from_due(row.next_due, threshold_days))
    )
    subj_alerts = sum(
        1
        for row in QualificationCycle.objects.filter(kind=QualificationCycle.Kind.SUBJECTIVE)
        if is_compliance_alert_status(status_from_due(row.next_due, threshold_days))
    )
    navdata_alerts = 0
    for device in Device.objects.select_related("navdata").all():
        record = getattr(device, "navdata", None)
        due = getattr(record, "next_due", None) if record else None
        if is_compliance_alert_status(status_from_due(due, threshold_days)):
            navdata_alerts += 1

    maint_alerts = sum(
        1
        for task in MaintenanceTask.objects.select_related("device")
        if is_compliance_alert_status(maintenance_task_status(task, threshold_days))
    )

    def finding_card_tone(qs) -> str:
        if qs.filter(due_date__lt=date.today()).exists():
            return "bad"
        if qs.exists():
            return "warn"
        return "good"

    def hil_card_tone() -> str:
        if open_hil.filter(due_date__lt=date.today()).exists():
            return "bad"
        if open_hil.exists():
            return "warn"
        return "good"

    return [
        _stat_card(devices.count(), "FSTD devices"),
        _stat_card(qtg_alerts, "QTG revalidations due/overdue", "warn" if qtg_alerts else "good"),
        _stat_card(
            subj_alerts, "Subjective tests due/overdue", "warn" if subj_alerts else "good"
        ),
        _stat_card(navdata_alerts, "Navdata due/overdue", "warn" if navdata_alerts else "good"),
        _stat_card(
            maint_alerts, "Maintenance tasks due/overdue", "warn" if maint_alerts else "good"
        ),
        _stat_card(open_hil.count(), "Open hold items", hil_card_tone()),
        _stat_card(open_authority.count(), "Open authority findings", finding_card_tone(open_authority)),
        _stat_card(
            open_internal.count(), "Open internal audit findings", finding_card_tone(open_internal)
        ),
        _stat_card(Document.objects.count(), "Documents on file"),
    ]


def dashboard_chart_data() -> dict[str, list[dict[str, Any]]]:
    from apps.findings.models import Finding
    from apps.operations.models import HoldItem

    status_colors = {
        Finding.Status.OPEN: "#dc2626",
        Finding.Status.IN_PROGRESS: "#d99a3c",
        Finding.Status.AWAITING: "#94a3b8",
        Finding.Status.CLOSED: "#16a34a",
    }
    status_counts = Counter(Finding.objects.values_list("status", flat=True))
    chart_status = [
        {"label": label, "value": status_counts.get(label, 0), "color": color}
        for label, color in status_colors.items()
    ]

    open_findings = Finding.objects.exclude(status=Finding.Status.CLOSED)
    cat_counts = Counter(open_findings.values_list("category", flat=True))
    chart_category = [
        {"label": label, "value": value, "color": "#d99a3c"}
        for label, value in cat_counts.most_common(8)
    ]

    dev_counts: Counter = Counter()
    for finding in open_findings.filter(device__isnull=False).select_related("device"):
        dev_counts[finding.device.name] += 1
    for hil in HoldItem.objects.filter(closure_date__isnull=True).select_related("device"):
        dev_counts[hil.device.name] += 1

    chart_device = [
        {"label": label, "value": value, "color": "#1e3450"}
        for label, value in dev_counts.most_common()
    ]

    return {
        "chart_status": chart_status,
        "chart_status_total": sum(item["value"] for item in chart_status),
        "chart_status_gradient": donut_conic_gradient(chart_status),
        "chart_category": chart_category,
        "chart_category_max": max((item["value"] for item in chart_category), default=0),
        "chart_device": chart_device,
        "chart_device_max": max((item["value"] for item in chart_device), default=0),
    }


def donut_conic_gradient(data: list[dict[str, Any]]) -> str:
    total = sum(item["value"] for item in data)
    if total == 0:
        return ""
    acc = 0
    stops = []
    for item in data:
        if item["value"] <= 0:
            continue
        start = acc / total * 360
        acc += item["value"]
        end = acc / total * 360
        stops.append(f"{item['color']} {start:.2f}deg {end:.2f}deg")
    return ", ".join(stops)


def count_maintenance_alerts(threshold_days: int = 30) -> int:
    from apps.operations.models import MaintenanceTask

    return sum(
        1
        for task in MaintenanceTask.objects.select_related("device")
        if is_compliance_alert_status(maintenance_task_status(task, threshold_days))
    )


def count_navdata_alerts(threshold_days: int = 30) -> int:
    from apps.devices.models import Device

    count = 0
    for device in Device.objects.select_related("navdata").all():
        record = getattr(device, "navdata", None)
        due = getattr(record, "next_due", None) if record else None
        if is_compliance_alert_status(status_from_due(due, threshold_days)):
            count += 1
    return count


def maintenance_list_row(task, threshold_days: int = 30) -> dict[str, Any]:
    from django.urls import reverse

    kind = task.kind
    status = maintenance_task_status(task, threshold_days)
    edit_url = reverse("operations:maintenance_edit", kwargs={"pk": task.pk})
    row = {
        "task": task,
        "kind": kind,
        "status": status,
        "edit_url": edit_url,
        "renew_url": f"{edit_url}?renew=1",
        "primary_label": "Renew",
    }
    if kind == "as_required":
        row.update(
            {
                "last_display": task.last_completed or "—",
                "due_mode": "on_demand",
                "show_status_dash": True,
                "primary_label": "Log entry",
            }
        )
        return row
    if kind == "hours":
        definition = task.definition or {}
        interval = definition.get("hours_interval", 0)
        base = task.last_service_hours_minutes
        current = task.device.current_hours_minutes or 0
        row["last_display"] = minutes_to_hours_display(base) if base is not None else "—"
        if base is not None:
            due_hours = (base + interval * 60) / 60
            current_hours = current / 60
            row["due_display"] = f"{current_hours:.0f} / {due_hours:.0f} hrs"
        else:
            row["due_display"] = "—"
        row["due_mode"] = "hours"
        return row
    row.update(
        {
            "last_display": task.last_completed or "—",
            "due_display": task.next_due or "—",
            "due_mode": "date",
        }
    )
    return row


def count_cycle_alerts(kind: str, threshold_days: int = 30) -> int:
    from apps.qualification.models import QualificationCycle

    return sum(
        1
        for row in QualificationCycle.objects.filter(kind=kind)
        if is_compliance_alert_status(status_from_due(row.next_due, threshold_days))
    )


def list_view_query_string(request, **overrides) -> str:
    params = request.GET.copy()
    for key, value in overrides.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = str(value)
    return params.urlencode()


LIST_FILTER_SESSION_KEY = "list_filters"


def remember_list_filters(request, list_url_name: str) -> None:
    filters = dict(request.session.get(LIST_FILTER_SESSION_KEY) or {})
    filters[list_url_name] = request.GET.urlencode()
    request.session[LIST_FILTER_SESSION_KEY] = filters


def clear_list_filters(request, list_url_name: str) -> None:
    filters = dict(request.session.get(LIST_FILTER_SESSION_KEY) or {})
    if list_url_name not in filters:
        return
    filters.pop(list_url_name)
    request.session[LIST_FILTER_SESSION_KEY] = filters


def remembered_list_url(request, list_url_name: str) -> str:
    from django.urls import reverse

    url = reverse(list_url_name)
    filters = request.session.get(LIST_FILTER_SESSION_KEY) or {}
    query = filters.get(list_url_name)
    if query:
        return f"{url}?{query}"
    return url


def archive_years_for(queryset) -> list[int]:
    from django.db.models.functions import ExtractYear

    return list(
        queryset.filter(archived_at__isnull=False)
        .annotate(year=ExtractYear("archived_at"))
        .values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )


def selected_archive_year(request, years: list[int]) -> int:
    requested = request.GET.get("year")
    if requested and requested.isdigit():
        year = int(requested)
        if year in years:
            return year
    if years:
        current = date.today().year
        return current if current in years else years[0]
    return date.today().year
