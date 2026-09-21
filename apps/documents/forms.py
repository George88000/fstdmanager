from django import forms

from apps.core.constants import FOLDER_ICON_CHOICES
from apps.core.forms import StyledFormMixin
from apps.documents.models import Document, Folder


class FolderForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Folder
        fields = ["name", "icon"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["icon"].widget = forms.Select(choices=[(i, i) for i in FOLDER_ICON_CHOICES])


class DocumentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ["file", "folder", "device", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = True
        self.fields["device"].required = False
        self.fields["device"].empty_label = "General"
