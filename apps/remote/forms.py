from django import forms

from apps.core.forms import StyledFormMixin
from apps.remote.models import RemoteConnection


class RemoteConnectionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = RemoteConnection
        fields = ["label", "anydesk_id", "password", "devices", "notes"]
        labels = {"anydesk_id": "AnyDesk ID"}
        widgets = {"devices": forms.CheckboxSelectMultiple}
