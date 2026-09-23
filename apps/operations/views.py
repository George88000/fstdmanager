from datetime import date

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.models import OrganizationSettings
from apps.core.utils import (
    archive_years_for,
    list_view_query_string,
    maintenance_list_row,
    remembered_list_url,
    selected_archive_year,
)
from apps.core.views import RemembersListFiltersMixin, ReturnsToFilteredListMixin
from apps.devices.models import Device
from apps.documents.models import Document
from apps.operations.forms import HoldItemForm, MaintenanceTaskForm, PermanentDefectForm
from apps.operations.models import HoldItem, MaintenanceEvent, MaintenanceTask, PermanentDefect


class HoldItemListView(RemembersListFiltersMixin, ListView):
    model = HoldItem
    template_name = "operations/holditem_list.html"
    context_object_name = "items"

    def get_queryset(self):
        qs = HoldItem.objects.select_related("device")
        archive_mode = self.request.GET.get("view") == "archive"
        if archive_mode:
            year = selected_archive_year(self.request, archive_years_for(HoldItem.objects.all()))
            qs = qs.filter(archived_at__isnull=False, archived_at__year=year)
        else:
            qs = qs.filter(archived_at__isnull=True)
        device = self.request.GET.get("device")
        if device and device != "all":
            qs = qs.filter(device_id=device)
        status = self.request.GET.get("status")
        if status == "Open":
            qs = qs.filter(closure_date__isnull=True)
        elif status == "Closed":
            qs = qs.exclude(closure_date__isnull=True)
        category = self.request.GET.get("category")
        if category and category != "all":
            qs = qs.filter(defect_category=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        threshold = OrganizationSettings.get_solo().threshold_days
        archive_years = archive_years_for(HoldItem.objects.all())
        archive_mode = self.request.GET.get("view") == "archive"
        selected_year = selected_archive_year(self.request, archive_years) if archive_mode else None
        context.update(
            {
                "page_title": "Hold Item List",
                "page_desc": "Deferred defects from the technical log",
                "threshold": threshold,
                "devices": Device.objects.all(),
                "categories": HoldItem.Category.choices,
                "archive_mode": archive_mode,
                "archive_years": archive_years,
                "selected_year": selected_year,
                "active_tab_query": list_view_query_string(self.request, view=None, year=None),
                "archive_tab_query": list_view_query_string(
                    self.request,
                    view="archive",
                    year=selected_archive_year(self.request, archive_years),
                ),
            }
        )
        return context


class HoldItemArchiveView(View):
    def post(self, request, pk):
        item = get_object_or_404(HoldItem, pk=pk)
        list_url = remembered_list_url(request, "operations:hold_items")
        if item.closure_date is None:
            messages.error(request, "Only closed hold items can be archived.")
            return redirect(list_url)
        if item.archived_at:
            messages.warning(request, "Hold item is already archived.")
            return redirect(list_url)
        item.archived_at = timezone.now()
        item.updated_by = request.user
        item.save(update_fields=["archived_at", "updated_by", "updated_at"])
        messages.success(request, f"Hold item archived to {item.archived_at.year} archive.")
        return redirect(list_url)


class HoldItemCreateView(ReturnsToFilteredListMixin, CreateView):
    model = HoldItem
    form_class = HoldItemForm
    template_name = "operations/holditem_form.html"
    list_url_name = "operations:hold_items"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Log hold item", "page_desc": ""})
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Hold item logged.")
        return super().form_valid(form)


class HoldItemUpdateView(ReturnsToFilteredListMixin, UpdateView):
    model = HoldItem
    form_class = HoldItemForm
    template_name = "operations/holditem_form.html"
    list_url_name = "operations:hold_items"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": f"Item {self.object.seq}", "page_desc": self.object.device.name})
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Hold item saved.")
        return super().form_valid(form)


class HoldItemInfoView(DetailView):
    model = HoldItem
    template_name = "operations/holditem_info.html"

    def render_to_response(self, context, **response_kwargs):
        html = render_to_string(self.template_name, context, request=self.request)
        return HttpResponse(html)


class HoldItemDeleteView(ReturnsToFilteredListMixin, DeleteView):
    model = HoldItem
    template_name = "operations/confirm_delete.html"
    list_url_name = "operations:hold_items"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Delete hold item"})
        return context


class PermanentDefectListView(RemembersListFiltersMixin, ListView):
    model = PermanentDefect
    template_name = "operations/permanentdefect_list.html"
    context_object_name = "items"

    def get_queryset(self):
        qs = PermanentDefect.objects.select_related("device")
        device = self.request.GET.get("device")
        if device and device != "all":
            qs = qs.filter(device_id=device)
        category = self.request.GET.get("category")
        if category and category != "all":
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = OrganizationSettings.get_solo()
        context.update(
            {
                "page_title": "Permanent Defects",
                "page_desc": "Accepted defects that will not be corrected",
                "devices": Device.objects.all(),
                "categories": settings.finding_categories or [],
            }
        )
        return context


class PermanentDefectInfoView(DetailView):
    model = PermanentDefect
    template_name = "operations/permanentdefect_info.html"

    def render_to_response(self, context, **response_kwargs):
        html = render_to_string(self.template_name, context, request=self.request)
        return HttpResponse(html)


class PermanentDefectCreateView(ReturnsToFilteredListMixin, CreateView):
    model = PermanentDefect
    form_class = PermanentDefectForm
    template_name = "operations/permanentdefect_form.html"
    list_url_name = "operations:permanent_defects"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Log permanent defect", "page_desc": ""})
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Permanent defect logged.")
        return super().form_valid(form)


class PermanentDefectUpdateView(ReturnsToFilteredListMixin, UpdateView):
    model = PermanentDefect
    form_class = PermanentDefectForm
    template_name = "operations/permanentdefect_form.html"
    list_url_name = "operations:permanent_defects"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Edit permanent defect", "page_desc": self.object.title})
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Permanent defect saved.")
        return super().form_valid(form)


class PermanentDefectDeleteView(ReturnsToFilteredListMixin, DeleteView):
    model = PermanentDefect
    template_name = "operations/confirm_delete.html"
    list_url_name = "operations:permanent_defects"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Delete permanent defect"})
        return context


class MaintenanceListView(RemembersListFiltersMixin, ListView):
    model = MaintenanceTask
    template_name = "operations/maintenance_list.html"
    context_object_name = "rows"

    def get_queryset(self):
        return MaintenanceTask.objects.select_related("device").exclude(device__maintenance_program="")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        threshold = OrganizationSettings.get_solo().threshold_days
        device_id = self.request.GET.get("device")
        status_filter = self.request.GET.get("status", "all")

        rows = []
        for task in self.object_list:
            if device_id and device_id != "all" and str(task.device_id) != device_id:
                continue
            row = maintenance_list_row(task, threshold)
            if status_filter == "over" and row["status"] != "over":
                continue
            if status_filter == "soon" and row["status"] != "soon":
                continue
            if status_filter == "ok" and row["status"] not in {"ok", "none"}:
                continue
            rows.append(row)

        programmed_devices = Device.objects.exclude(maintenance_program="")
        context.update(
            {
                "page_title": "Maintenance",
                "page_desc": "Preventive maintenance tasks by device programme",
                "threshold": threshold,
                "rows": rows,
                "devices": programmed_devices,
                "has_programmed_devices": programmed_devices.exists(),
            }
        )
        return context


class MaintenanceUpdateView(ReturnsToFilteredListMixin, UpdateView):
    model = MaintenanceTask
    form_class = MaintenanceTaskForm
    template_name = "operations/maintenance_form.html"
    list_url_name = "operations:maintenance"

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get("renew") == "1":
            today = date.today()
            if self.object.kind == "as_required":
                initial["last_completed"] = today
            elif self.object.kind == "hours":
                initial["last_service_hours_minutes"] = self.object.device.current_hours_minutes
                initial["last_completed"] = today
            else:
                initial["last_completed"] = today
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_renew = self.request.GET.get("renew") == "1" or self.request.POST.get("renew") == "1"
        is_log_entry = self.object.kind == "as_required"
        if is_log_entry:
            title = f"Log entry — {self.object.task_name}"
        elif is_renew:
            title = f"Renew — {self.object.task_name}"
        else:
            title = f"Edit — {self.object.task_name}"
        context.update(
            {
                "page_title": title,
                "page_desc": self.object.device.name,
                "history": self.object.history.all(),
                "attachments": self.object.attachments.all(),
                "is_renew": is_renew,
                "is_log_entry": is_log_entry,
            }
        )
        return context

    def form_valid(self, form):
        task = self.get_object()
        renew = self.request.POST.get("renew") == "1"
        if renew and task.last_completed:
            MaintenanceEvent.objects.create(
                task=task,
                date=task.last_completed,
                notes=task.notes,
                service_hours_minutes=task.last_service_hours_minutes,
            )
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Maintenance task saved.")
        response = super().form_valid(form)
        upload = self.request.FILES.get("attachment")
        if upload:
            Document.objects.create(
                file=upload,
                original_name=upload.name,
                mime=upload.content_type or "",
                size=upload.size,
                maintenance_task=self.object,
                device=self.object.device,
                created_by=self.request.user,
            )
        return response
