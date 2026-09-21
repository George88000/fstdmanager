from django import forms

from apps.core.forms import StyledFormMixin
from apps.qualification.models import NavdataRecord, QualificationCycle


class CycleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = QualificationCycle
        fields = ["last_completed", "next_due", "notes"]
        widgets = {
            "last_completed": forms.DateInput(attrs={"type": "date"}),
            "next_due": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["last_completed"].required = True


class NavdataForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = NavdataRecord
        fields = ["last_updated", "cycle_ref", "notes"]
        widgets = {"last_updated": forms.DateInput(attrs={"type": "date"})}
        labels = {"cycle_ref": "AIRAC / cycle ref"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["last_updated"].required = True
