from django import template

from apps.core.utils import days_until, maintenance_task_status, status_from_due

register = template.Library()


@register.inclusion_tag("includes/status_pill.html")
def due_pill(due, threshold=30, status=None):
    resolved = status or status_from_due(due, threshold or 30)
    remaining = days_until(due)
    extra = ""
    if due and remaining is not None:
        if resolved == "over":
            extra = f" ({abs(remaining)}d overdue)"
        elif resolved == "soon":
            extra = f" ({remaining}d left)"
    return {"status": resolved, "extra": extra}


@register.inclusion_tag("includes/status_pill.html")
def maint_pill(task, threshold=30):
    resolved = maintenance_task_status(task, threshold or 30)
    due = task.next_due if task.kind not in {"hours", "as_required"} else None
    remaining = days_until(due)
    extra = ""
    if due and remaining is not None:
        if resolved == "over":
            extra = f" ({abs(remaining)}d overdue)"
        elif resolved == "soon":
            extra = f" ({remaining}d left)"
    return {"status": resolved, "extra": extra}


@register.inclusion_tag("includes/class_pill.html")
def class_pill(value):
    return {"value": value}


@register.inclusion_tag("includes/kind_pill.html")
def kind_pill(value):
    return {"value": value}


@register.inclusion_tag("includes/finding_status_pill.html")
def finding_status_pill(status):
    return {"status": status}
