from django import forms

from apps.core.forms import HoursMinutesField, StyledFormMixin
from apps.devices.models import Device


class DeviceForm(StyledFormMixin, forms.ModelForm):
    current_hours_minutes = HoursMinutesField(
        label="Current simulator hours",
        help_text="Format HHHH:MM (or a plain number of hours).",
    )

    class Meta:
        model = Device
        fields = [
            "name",
            "type",
            "level",
            "manufacturer",
            "serial",
            "location",
            "navdata_cycle",
            "current_hours_minutes",
            "maintenance_program",
            "notes",
        ]
        labels = {
            "name": "Device name",
            "serial": "Serial / registration",
            "location": "Location / bay",
            "navdata_cycle": "Navdata validity",
        }

    def clean_current_hours_minutes(self):
        return self.cleaned_data.get("current_hours_minutes") or 0
