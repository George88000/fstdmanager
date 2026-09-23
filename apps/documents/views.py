from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.constants import STANDARD_FOLDERS
from apps.documents.forms import DocumentForm, DocumentMoveForm, FolderForm
from apps.documents.models import Document, Folder


def ensure_standard_folders():
    for item in STANDARD_FOLDERS:
        Folder.objects.get_or_create(
            name=item["name"],
            parent=None,
            defaults={"icon": item["icon"], "is_standard": True},
        )


def folder_return_url(folder):
    if folder:
        return reverse("documents:folder", args=[folder.pk])
    return reverse("documents:list")


class FolderListView(ListView):
    model = Folder
    template_name = "documents/folder_list.html"
    context_object_name = "folders"

    def get_queryset(self):
        ensure_standard_folders()
        return Folder.objects.filter(parent__isnull=True).annotate(
            document_count=Count("documents", distinct=True),
            child_count=Count("children", distinct=True),
        )

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

    def dispatch(self, request, *args, **kwargs):
        self.parent = None
        parent_id = request.GET.get("parent")
        if parent_id:
            self.parent = get_object_or_404(Folder, pk=parent_id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["parent"] = self.parent
        return kwargs

    def get_success_url(self):
        return folder_return_url(self.object.parent)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.parent:
            context.update(
                {
                    "page_title": "New subfolder",
                    "page_desc": self.parent.display_path(),
                    "cancel_url": folder_return_url(self.parent),
                }
            )
        else:
            context.update(
                {
                    "page_title": "New folder",
                    "page_desc": "",
                    "cancel_url": reverse("documents:list"),
                }
            )
        return context

    def form_valid(self, form):
        form.instance.parent = self.parent
        messages.success(self.request, "Folder created.")
        return super().form_valid(form)


class FolderDeleteView(DeleteView):
    model = Folder
    template_name = "documents/confirm_delete.html"
    success_url = reverse_lazy("documents:list")

    def get_queryset(self):
        return Folder.objects.filter(is_standard=False)

    def get_success_url(self):
        parent_id = getattr(self, "_redirect_parent_id", None)
        if parent_id:
            return reverse("documents:folder", args=[parent_id])
        return reverse("documents:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Delete folder",
                "cancel_url": reverse("documents:folder", args=[self.object.pk]),
            }
        )
        return context

    def form_valid(self, form):
        folder = self.object
        colliding = folder.colliding_child_names_on_delete()
        if colliding:
            messages.error(
                self.request,
                f"Cannot delete this folder: {', '.join(colliding)} already exists at the destination level.",
            )
            return redirect("documents:folder", pk=folder.pk)
        self._redirect_parent_id = folder.parent_id
        messages.success(self.request, "Folder deleted.")
        return super().form_valid(form)


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
                "subfolders": self.folder.children.annotate(
                    document_count=Count("documents", distinct=True),
                    child_count=Count("children", distinct=True),
                ),
                "breadcrumbs": self.folder.ancestors(),
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


class DocumentMoveView(UpdateView):
    model = Document
    form_class = DocumentMoveForm
    template_name = "documents/document_move.html"

    def get_success_url(self):
        if self.object.folder_id:
            return reverse("documents:folder", args=[self.object.folder_id])
        return reverse("documents:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.folder_id:
            cancel_url = reverse("documents:folder", args=[self.object.folder_id])
        else:
            cancel_url = reverse("documents:list")
        context.update(
            {
                "page_title": f"Move {self.object.original_name}",
                "page_desc": "",
                "cancel_url": cancel_url,
            }
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, "Document moved.")
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
