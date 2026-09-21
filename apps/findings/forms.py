from django import forms

from apps.core.forms import StyledFormMixin
from apps.core.models import OrganizationSettings
from apps.findings.models import Finding


class FindingForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Finding
        fields = [
            "title",
            "category",
            "cls",
            "kind",
            "device",
            "authority",
            "date_raised",
            "due_date",
            "status",
            "description",
            "resolution",
            "closure_evidence",
        ]
        widgets = {
            "date_raised": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "cls": "Class",
            "authority": "Authority / auditor",
            "due_date": "Corrective action due",
            "closure_evidence": "Closure evidence",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cats = OrganizationSettings.get_solo().finding_categories or []
        self.fields["category"].widget = forms.Select(choices=[(c, c) for c in cats])
        self.fields["device"].required = False
        self.fields["device"].empty_label = "General / not device-specific"
