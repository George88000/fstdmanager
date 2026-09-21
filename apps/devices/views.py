from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.models import OrganizationSettings
from apps.core.utils import status_from_due
from apps.devices.forms import DeviceForm
from apps.devices.models import Device
from apps.findings.models import Finding
from apps.qualification.models import QualificationCycle


class DeviceListView(ListView):
    model = Device
    template_name = "devices/device_list.html"
    context_object_name = "devices"

    def get_queryset(self):
        return Device.objects.prefetch_related("cycles", "findings", "navdata").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        threshold = OrganizationSettings.get_solo().threshold_days
        rows = []
        for device in context["devices"]:
            qtg = next((c for c in device.cycles.all() if c.kind == QualificationCycle.Kind.QTG), None)
            subj = next((c for c in device.cycles.all() if c.kind == QualificationCycle.Kind.SUBJECTIVE), None)
            rows.append(
                {
                    "device": device,
                    "qtg": qtg,
                    "qtg_status": status_from_due(qtg.next_due if qtg else None, threshold),
                    "subj": subj,
                    "subj_status": status_from_due(subj.next_due if subj else None, threshold),
                    "open_findings": sum(
                        1 for f in device.findings.all() if f.status != Finding.Status.CLOSED
                    ),
                }
            )
        context.update(
            {
                "page_title": "FSTD Devices",
                "page_desc": "Qualified training devices and their status snapshot",
                "rows": rows,
            }
        )
        return context


class DeviceCreateView(CreateView):
    model = Device
    form_class = DeviceForm
    template_name = "devices/device_form.html"
    success_url = reverse_lazy("devices:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Add FSTD", "page_desc": "Register a new training device"})
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Device added.")
        return super().form_valid(form)


class DeviceUpdateView(UpdateView):
    model = Device
    form_class = DeviceForm
    template_name = "devices/device_form.html"
    success_url = reverse_lazy("devices:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Edit FSTD", "page_desc": self.object.name})
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Device saved.")
        return super().form_valid(form)


class DeviceDeleteView(DeleteView):
    model = Device
    template_name = "devices/device_confirm_delete.html"
    success_url = reverse_lazy("devices:list")

    def form_valid(self, form):
        messages.success(self.request, "Device deleted.")
        return super().form_valid(form)
