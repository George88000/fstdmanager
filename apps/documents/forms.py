from django import forms
from django.db.models import Case, IntegerField, When

from apps.core.constants import FOLDER_ICON_CHOICES
from apps.core.forms import StyledFormMixin
from apps.documents.models import Document, Folder


def iter_folders_tree():
    roots = Folder.objects.filter(parent__isnull=True).order_by("-is_standard", "name")
    result = []

    def walk(folder, depth):
        result.append((folder, depth))
        for child in folder.children.order_by("name"):
            walk(child, depth + 1)

    for root in roots:
        walk(root, 0)
    return result


def folder_choice_label(folder, depth):
    if depth == 0:
        return folder.name
    indent = "\u00a0\u00a0" * depth
    return f"{indent}— {folder.name}"


def apply_folder_choices(field):
    tree = iter_folders_tree()
    if not tree:
        field.queryset = Folder.objects.none()
        return

    ordered_pks = [folder.pk for folder, _ in tree]
    labels = {folder.pk: folder_choice_label(folder, depth) for folder, depth in tree}
    ordering = Case(
        *[When(pk=pk, then=position) for position, pk in enumerate(ordered_pks)],
        output_field=IntegerField(),
    )
    field.queryset = Folder.objects.filter(pk__in=ordered_pks).order_by(ordering)
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


class DocumentEditForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ["original_name", "device"]
        labels = {
            "original_name": "File name",
            "device": "Related device",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["original_name"].required = True
        self.fields["device"].required = False
        self.fields["device"].empty_label = "General"
