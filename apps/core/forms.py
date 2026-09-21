from django import forms

from apps.core.models import OrganizationSettings
from apps.core.utils import hours_to_minutes, minutes_to_hours_display

INPUT_CLASS = (
    "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm "
    "text-navy-900 focus:outline-none focus:ring-2 focus:ring-amber/50"
)


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(
                widget,
                (
                    forms.CheckboxInput,
                    forms.CheckboxSelectMultiple,
                    forms.ClearableFileInput,
                    forms.FileInput,
                    forms.HiddenInput,
                ),
            ):
                continue
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {INPUT_CLASS}".strip()
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("rows", 4)


class HoursMinutesField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if value in (None, ""):
            return ""
        if isinstance(value, int):
            return minutes_to_hours_display(value)
        return value

    def clean(self, value):
        value = super().clean(value)
        if value in (None, ""):
            return None
        try:
            return hours_to_minutes(value)
        except (TypeError, ValueError) as exc:
            raise forms.ValidationError("Use HHHH:MM or a number of hours.") from exc


class SettingsForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = OrganizationSettings
        fields = ["ato_name", "threshold_days"]
        labels = {
            "ato_name": "ATO / organisation name",
            "threshold_days": 'Alert threshold (days before due to flag as "due soon")',
        }


class CategoryForm(StyledFormMixin, forms.Form):
    new_category = forms.CharField(label="New category name", max_length=80, required=True)
