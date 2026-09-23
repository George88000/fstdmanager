from django import forms

from apps.core.constants import FOLDER_ICON_CHOICES
from apps.core.forms import StyledFormMixin
from apps.documents.models import Document, Folder


def apply_folder_choices(field):
    folders = list(Folder.objects.select_related("parent"))
    labels = {folder.pk: folder.display_path() for folder in folders}
    field.queryset = Folder.objects.all()
    field.label_from_instance = lambda folder: labels.get(folder.pk, folder.name)


class FolderForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Folder
        fields = ["name", "icon"]

    def __init__(self, *args, parent=None, **kwargs):
        self.parent = parent
        super().__init__(*args, **kwargs)
        self.fields["icon"].widget = forms.Select(choices=[(i, i) for i in FOLDER_ICON_CHOICES])

    def clean_name(self):
        name = self.cleaned_data["name"]
        qs = Folder.objects.filter(name=name, parent=self.parent)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A folder with this name already exists at this level.")
        return name


class DocumentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ["file", "folder", "device", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = True
        self.fields["device"].required = False
        self.fields["device"].empty_label = "General"
        apply_folder_choices(self.fields["folder"])


class DocumentMoveForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ["folder"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_folder_choices(self.fields["folder"])
        self.fields["folder"].required = True
        self.fields["folder"].empty_label = None
