from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.models import OrganizationSettings
from apps.devices.models import Device
from apps.findings.forms import FindingForm
from apps.findings.models import Finding


class FindingListView(ListView):
    model = Finding
    template_name = "findings/finding_list.html"
    context_object_name = "findings"
    source = Finding.Source.AUTHORITY

    def get_queryset(self):
        qs = Finding.objects.select_related("device").filter(source=self.source)
        status = self.request.GET.get("status")
        if status and status != "all":
            qs = qs.filter(status=status)
        category = self.request.GET.get("category")
        if category and category != "all":
            qs = qs.filter(category=category)
        device = self.request.GET.get("device")
        if device == "general":
            qs = qs.filter(device__isnull=True)
        elif device and device != "all":
            qs = qs.filter(device_id=device)
        cls = self.request.GET.get("cls")
        if cls and cls != "all":
            qs = qs.filter(cls=cls)
        kind = self.request.GET.get("kind")
        if kind and kind != "all":
            qs = qs.filter(kind=kind)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.source == Finding.Source.INTERNAL:
            title, desc = "Internal Audit Findings", "Findings from internal audits"
            add_url = "findings:internal_add"
            edit_name = "findings:internal_edit"
        else:
            title, desc = "Authority Findings", "Findings raised by the competent authority"
            add_url = "findings:authority_add"
            edit_name = "findings:authority_edit"
        settings = OrganizationSettings.get_solo()
        context.update(
            {
                "page_title": title,
                "page_desc": desc,
                "source": self.source,
                "add_url": add_url,
                "edit_name": edit_name,
                "info_name": edit_name.replace("_edit", "_info"),
                "status_choices": Finding.Status.choices,
                "class_choices": Finding.Cls.choices,
                "kind_choices": Finding.Kind.choices,
                "categories": settings.finding_categories or [],
                "devices": Device.objects.all(),
            }
        )
        return context


class FindingInfoView(DetailView):
    model = Finding
    template_name = "findings/finding_info.html"
    source = Finding.Source.AUTHORITY

    def get_queryset(self):
        return Finding.objects.filter(source=self.source)

    def render_to_response(self, context, **response_kwargs):
        html = render_to_string(self.template_name, context, request=self.request)
        return HttpResponse(html)


class FindingCreateView(CreateView):
    model = Finding
    form_class = FindingForm
    template_name = "findings/finding_form.html"
    source = Finding.Source.AUTHORITY

    def get_success_url(self):
        return reverse("findings:internal" if self.source == Finding.Source.INTERNAL else "findings:authority")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        label = "internal audit" if self.source == Finding.Source.INTERNAL else "authority"
        context.update({"page_title": f"Log {label} finding", "page_desc": "", "source": self.source})
        return context

    def form_valid(self, form):
        form.instance.source = self.source
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Finding logged.")
        return super().form_valid(form)


class FindingUpdateView(UpdateView):
    model = Finding
    form_class = FindingForm
    template_name = "findings/finding_form.html"
    source = Finding.Source.AUTHORITY

    def get_queryset(self):
        return Finding.objects.filter(source=self.source)

    def get_success_url(self):
        return reverse("findings:internal" if self.source == Finding.Source.INTERNAL else "findings:authority")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": self.object.ref, "page_desc": self.object.title, "source": self.source})
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Finding saved.")
        return super().form_valid(form)


class FindingDeleteView(DeleteView):
    model = Finding
    template_name = "findings/finding_confirm_delete.html"
    source = Finding.Source.AUTHORITY

    def get_queryset(self):
        return Finding.objects.filter(source=self.source)

    def get_success_url(self):
        return reverse("findings:internal" if self.source == Finding.Source.INTERNAL else "findings:authority")

    def form_valid(self, form):
        messages.success(self.request, "Finding deleted.")
        return super().form_valid(form)
