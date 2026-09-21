from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, UpdateView

from apps.core.models import OrganizationSettings
from apps.core.utils import add_months, status_from_due
from apps.devices.models import Device
from apps.qualification.forms import CycleForm, NavdataForm
from apps.qualification.models import NavdataEvent, NavdataRecord, QualificationCycle, QualificationEvent


class CycleListView(ListView):
    template_name = "qualification/cycle_list.html"
    context_object_name = "rows"
    kind = QualificationCycle.Kind.QTG

    def get_queryset(self):
        return Device.objects.prefetch_related("cycles").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        threshold = OrganizationSettings.get_solo().threshold_days
        kind = self.kind
        rows = []
        edit_name = (
            "qualification:qtg_edit"
            if kind == QualificationCycle.Kind.QTG
            else "qualification:subjective_edit"
        )
        for device in self.object_list:
            cycle = next((c for c in device.cycles.all() if c.kind == kind), None)
            edit_url = reverse(edit_name, kwargs={"device_id": device.pk})
            rows.append(
                {
                    "device": device,
                    "cycle": cycle,
                    "status": status_from_due(cycle.next_due if cycle else None, threshold),
                    "edit_url": edit_url,
                    "renew_url": f"{edit_url}?renew=1",
                }
            )
        titles = {
            QualificationCycle.Kind.QTG: ("QTG Validation", "Objective test cycles per device"),
            QualificationCycle.Kind.SUBJECTIVE: ("Subjective Tests", "Subjective evaluation cycles per device"),
        }
        title, desc = titles[kind]
        context.update(
            {
                "page_title": title,
                "page_desc": desc,
                "rows": rows,
                "kind": kind,
                "edit_url_name": "qualification:qtg_edit"
                if kind == QualificationCycle.Kind.QTG
                else "qualification:subjective_edit",
            }
        )
        return context


class CycleUpdateView(UpdateView):
    model = QualificationCycle
    form_class = CycleForm
    template_name = "qualification/cycle_form.html"
    kind = QualificationCycle.Kind.QTG
    pk_url_kwarg = "device_id"

    def get_object(self, queryset=None):
        device = get_object_or_404(Device, pk=self.kwargs["device_id"])
        cycle, _ = QualificationCycle.objects.get_or_create(device=device, kind=self.kind)
        return cycle

    def get_success_url(self):
        if self.kind == QualificationCycle.Kind.QTG:
            return reverse("qualification:qtg")
        return reverse("qualification:subjective")

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get("renew") == "1":
            today = date.today()
            initial["last_completed"] = today
            initial["next_due"] = add_months(today, 3)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_renew = self.request.GET.get("renew") == "1" or self.request.POST.get("renew") == "1"
        kind_label = "QTG" if self.kind == QualificationCycle.Kind.QTG else "Subjective test"
        context.update(
            {
                "page_title": f"Renew {kind_label} — {self.object.device.name}"
                if is_renew
                else f"Edit {kind_label} — {self.object.device.name}",
                "page_desc": self.object.device.name,
                "history": self.object.history.all(),
                "is_renew": is_renew,
                "cancel_url": self.get_success_url(),
            }
        )
        return context

    def form_valid(self, form):
        cycle = self.get_object()
        renew = self.request.POST.get("renew") == "1"
        if renew and cycle.last_completed:
            QualificationEvent.objects.create(
                cycle=cycle,
                date=cycle.last_completed,
                notes=cycle.notes,
            )
            if not form.cleaned_data.get("next_due") and form.cleaned_data.get("last_completed"):
                form.instance.next_due = add_months(form.cleaned_data["last_completed"], 3)
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Record saved.")
        return super().form_valid(form)


class NavdataListView(ListView):
    template_name = "qualification/navdata_list.html"
    context_object_name = "rows"

    def get_queryset(self):
        return Device.objects.select_related("navdata").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        threshold = OrganizationSettings.get_solo().threshold_days
        rows = []
        for device in self.object_list:
            rec = getattr(device, "navdata", None)
            edit_url = reverse("qualification:navdata_edit", kwargs={"device_id": device.pk})
            rows.append(
                {
                    "device": device,
                    "record": rec,
                    "status": status_from_due(rec.next_due if rec else None, threshold),
                    "edit_url": edit_url,
                    "renew_url": f"{edit_url}?renew=1",
                }
            )
        context.update(
            {
                "page_title": "Navdata",
                "page_desc": "Navigation database currency per device",
                "rows": rows,
            }
        )
        return context


class NavdataUpdateView(UpdateView):
    model = NavdataRecord
    form_class = NavdataForm
    template_name = "qualification/navdata_form.html"
    pk_url_kwarg = "device_id"

    def get_object(self, queryset=None):
        device = get_object_or_404(Device, pk=self.kwargs["device_id"])
        record, _ = NavdataRecord.objects.get_or_create(device=device)
        return record

    def get_success_url(self):
        return reverse("qualification:navdata")

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get("renew") == "1":
            initial["last_updated"] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_renew = self.request.GET.get("renew") == "1" or self.request.POST.get("renew") == "1"
        context.update(
            {
                "page_title": f"Renew Navdata — {self.object.device.name}"
                if is_renew
                else f"Edit Navdata — {self.object.device.name}",
                "page_desc": self.object.device.name,
                "history": self.object.history.all(),
                "is_renew": is_renew,
            }
        )
        return context

    def form_valid(self, form):
        record = self.get_object()
        renew = self.request.POST.get("renew") == "1"
        if renew and record.last_updated:
            NavdataEvent.objects.create(
                record=record,
                date=record.last_updated,
                cycle_ref=record.cycle_ref,
                notes=record.notes,
            )
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Navdata saved.")
        return super().form_valid(form)
