from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.remote.forms import RemoteConnectionForm
from apps.remote.models import RemoteConnection


class RemoteListView(ListView):
    model = RemoteConnection
    template_name = "remote/remote_list.html"
    context_object_name = "connections"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Remote Connection",
                "page_desc": "AnyDesk access to simulator hosts",
            }
        )
        return context


class RemoteCreateView(CreateView):
    model = RemoteConnection
    form_class = RemoteConnectionForm
    template_name = "remote/remote_form.html"
    success_url = reverse_lazy("remote:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Add remote connection", "page_desc": ""})
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Connection added.")
        return super().form_valid(form)


class RemoteUpdateView(UpdateView):
    model = RemoteConnection
    form_class = RemoteConnectionForm
    template_name = "remote/remote_form.html"
    success_url = reverse_lazy("remote:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Edit connection", "page_desc": self.object.label})
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Connection saved.")
        return super().form_valid(form)


class RemoteDeleteView(DeleteView):
    model = RemoteConnection
    template_name = "remote/confirm_delete.html"
    success_url = reverse_lazy("remote:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Delete connection", "cancel_url": reverse("remote:list")})
        return context
