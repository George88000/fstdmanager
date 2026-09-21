"""Context processors for layout and organization branding."""


def organization(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"organization": None}
    from apps.core.models import OrganizationSettings

    return {"organization": OrganizationSettings.get_solo()}


def sidebar_badges(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"sidebar_badges": {}}
    from apps.core.models import OrganizationSettings
    from apps.core.utils import (
        count_cycle_alerts,
        count_maintenance_alerts,
        count_navdata_alerts,
        is_compliance_alert_status,
        status_from_due,
    )
    from apps.findings.models import Finding
    from apps.operations.models import HoldItem
    from apps.qualification.models import QualificationCycle

    settings_obj = OrganizationSettings.get_solo()
    threshold = settings_obj.threshold_days

    hil_open = HoldItem.objects.filter(closure_date__isnull=True)
    hil_alerts = sum(
        1 for item in hil_open if is_compliance_alert_status(status_from_due(item.due_date, threshold))
    )

    return {
        "sidebar_badges": {
            "qtg": count_cycle_alerts(QualificationCycle.Kind.QTG, threshold),
            "subjective": count_cycle_alerts(QualificationCycle.Kind.SUBJECTIVE, threshold),
            "navdata": count_navdata_alerts(threshold),
            "maintenance": count_maintenance_alerts(threshold),
            "hil": hil_alerts,
            "findings": Finding.objects.filter(
                source=Finding.Source.AUTHORITY
            ).exclude(status=Finding.Status.CLOSED).count(),
            "internal": Finding.objects.filter(
                source=Finding.Source.INTERNAL
            ).exclude(status=Finding.Status.CLOSED).count(),
        }
    }
