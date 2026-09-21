from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView

from apps.core.constants import STANDARD_FOLDERS
from apps.documents.forms import DocumentForm, FolderForm
from apps.documents.models import Document, Folder


def ensure_standard_folders():
    for item in STANDARD_FOLDERS:
        Folder.objects.get_or_create(
            name=item["name"],
            defaults={"icon": item["icon"], "is_standard": True},
        )


class FolderListView(ListView):
    model = Folder
    template_name = "documents/folder_list.html"
    context_object_name = "folders"

    def get_queryset(self):
        ensure_standard_folders()
        return Folder.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Documentation",
                "page_desc": "Folders for manuals, reports and correspondence",
            }
        )
        return context


class FolderCreateView(CreateView):
    model = Folder
    form_class = FolderForm
    template_name = "documents/folder_form.html"
    success_url = reverse_lazy("documents:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "New folder", "page_desc": ""})
        return context

    def form_valid(self, form):
        messages.success(self.request, "Folder created.")
        return super().form_valid(form)


class FolderDeleteView(DeleteView):
    model = Folder
    template_name = "documents/confirm_delete.html"
    success_url = reverse_lazy("documents:list")

    def get_queryset(self):
        return Folder.objects.filter(is_standard=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Delete folder", "cancel_url": reverse("documents:list")})
        return context


class FolderDetailView(ListView):
    model = Document
    template_name = "documents/folder_detail.html"
    context_object_name = "documents"

    def dispatch(self, request, *args, **kwargs):
        self.folder = get_object_or_404(Folder, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Document.objects.filter(folder=self.folder)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "folder": self.folder,
                "page_title": self.folder.name,
                "page_desc": "Documents in this folder",
            }
        )
        return context


class DocumentCreateView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"

    def get_initial(self):
        initial = super().get_initial()
        folder_id = self.request.GET.get("folder")
        if folder_id:
            initial["folder"] = folder_id
        return initial

    def get_success_url(self):
        if self.object.folder_id:
            return reverse("documents:folder", args=[self.object.folder_id])
        return reverse("documents:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Upload document", "page_desc": ""})
        return context

    def form_valid(self, form):
        upload = form.cleaned_data["file"]
        form.instance.original_name = upload.name
        form.instance.mime = getattr(upload, "content_type", "") or ""
        form.instance.size = upload.size
        form.instance.created_by = self.request.user
        messages.success(self.request, "Document uploaded.")
        return super().form_valid(form)


class DocumentDeleteView(DeleteView):
    model = Document
    template_name = "documents/confirm_delete.html"

    def get_success_url(self):
        if self.object.folder_id:
            return reverse("documents:folder", args=[self.object.folder_id])
        return reverse("documents:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Delete document", "cancel_url": self.get_success_url()})
        return context
