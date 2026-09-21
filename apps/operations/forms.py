from django import forms

from apps.core.forms import HoursMinutesField, StyledFormMixin
from apps.core.models import OrganizationSettings
from apps.core.utils import maintenance_due_date
from apps.operations.models import HoldItem, MaintenanceTask, PermanentDefect


class HoldItemForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = HoldItem
        fields = [
            "device",
            "atl_log_item",
            "affected_version",
            "description",
            "initials_report",
            "report_date",
            "defect_category",
            "due_date",
            "closure_atl_log_item",
            "closure_hours",
            "closure_date",
            "initials_closure",
        ]
        widgets = {
            "report_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "closure_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "atl_log_item": "ATL log / item",
            "closure_atl_log_item": "Closure ATL log / item",
            "closure_hours": "FNPT hours at closure",
        }


class PermanentDefectForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = PermanentDefect
        fields = ["device", "title", "category", "date_noted", "reference", "description"]
        widgets = {"date_noted": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cats = OrganizationSettings.get_solo().finding_categories or []
        self.fields["category"].widget = forms.Select(
            choices=[("", "—")] + [(c, c) for c in cats]
        )


class MaintenanceTaskForm(StyledFormMixin, forms.ModelForm):
    last_service_hours_minutes = HoursMinutesField(
        label="Hours reading at this service",
        required=False,
    )

    class Meta:
        model = MaintenanceTask
        fields = ["last_completed", "next_due", "last_service_hours_minutes", "notes"]
        widgets = {
            "last_completed": forms.DateInput(attrs={"type": "date"}),
            "next_due": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        kind = self.instance.kind
        if kind == "hours":
            self.fields["last_service_hours_minutes"].required = True
            self.fields["next_due"].required = False
        elif kind == "as_required":
            self.fields["next_due"].required = False
            self.fields.pop("last_service_hours_minutes", None)
        else:
            self.fields["last_completed"].required = True
            self.fields.pop("last_service_hours_minutes", None)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.kind not in {"hours", "as_required"} and instance.last_completed and not instance.next_due:
            instance.next_due = maintenance_due_date(instance.kind, instance.last_completed)
        if commit:
            instance.save()
        return instance
