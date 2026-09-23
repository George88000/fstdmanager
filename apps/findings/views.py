from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.models import OrganizationSettings
from apps.core.utils import archive_years_for, list_view_query_string, remembered_list_url, selected_archive_year
from apps.core.views import RemembersListFiltersMixin, ReturnsToFilteredListMixin
from apps.devices.models import Device
from apps.findings.forms import FindingForm
from apps.findings.models import Finding


class FindingListView(RemembersListFiltersMixin, ListView):
    model = Finding
    template_name = "findings/finding_list.html"
    context_object_name = "findings"
    source = Finding.Source.AUTHORITY

    def get_queryset(self):
        qs = Finding.objects.select_related("device").filter(source=self.source)
        archive_mode = self.request.GET.get("view") == "archive"
        if archive_mode:
            year = selected_archive_year(
                self.request,
                archive_years_for(Finding.objects.filter(source=self.source)),
            )
            qs = qs.filter(archived_at__isnull=False, archived_at__year=year)
        else:
            qs = qs.filter(archived_at__isnull=True)
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
            list_url = "findings:internal"
            archive_name = "findings:internal_archive"
        else:
            title, desc = "Authority Findings", "Findings raised by the competent authority"
            add_url = "findings:authority_add"
            edit_name = "findings:authority_edit"
            list_url = "findings:authority"
            archive_name = "findings:authority_archive"
        settings = OrganizationSettings.get_solo()
        base_qs = Finding.objects.filter(source=self.source)
        archive_years = archive_years_for(base_qs)
        archive_mode = self.request.GET.get("view") == "archive"
        selected_year = selected_archive_year(self.request, archive_years) if archive_mode else None
        context.update(
            {
                "page_title": title,
                "page_desc": desc,
                "source": self.source,
                "add_url": add_url,
                "edit_name": edit_name,
                "info_name": edit_name.replace("_edit", "_info"),
                "archive_name": archive_name,
                "list_url": list_url,
                "status_choices": Finding.Status.choices,
                "class_choices": Finding.Cls.choices,
                "kind_choices": Finding.Kind.choices,
                "categories": settings.finding_categories or [],
                "devices": Device.objects.all(),
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


class FindingArchiveView(View):
    source = Finding.Source.AUTHORITY

    def post(self, request, pk):
        finding = get_object_or_404(Finding, pk=pk, source=self.source)
        list_url = remembered_list_url(
            request,
            "findings:internal" if self.source == Finding.Source.INTERNAL else "findings:authority",
        )
        if finding.status != Finding.Status.CLOSED:
            messages.error(request, "Only closed findings can be archived.")
            return redirect(list_url)
        if finding.archived_at:
            messages.warning(request, "Finding is already archived.")
            return redirect(list_url)
        finding.archived_at = timezone.now()
        finding.updated_by = request.user
        finding.save(update_fields=["archived_at", "updated_by", "updated_at"])
        messages.success(request, f"Finding archived to {finding.archived_at.year} archive.")
        return redirect(list_url)


class FindingInfoView(DetailView):
    model = Finding
    template_name = "findings/finding_info.html"
    source = Finding.Source.AUTHORITY

    def get_queryset(self):
        return Finding.objects.filter(source=self.source)

    def render_to_response(self, context, **response_kwargs):
        html = render_to_string(self.template_name, context, request=self.request)
        return HttpResponse(html)


class FindingFilteredListMixin(ReturnsToFilteredListMixin):
    def get_list_url_name(self):
        return "findings:internal" if self.source == Finding.Source.INTERNAL else "findings:authority"


class FindingCreateView(FindingFilteredListMixin, CreateView):
    model = Finding
    form_class = FindingForm
    template_name = "findings/finding_form.html"
    source = Finding.Source.AUTHORITY

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


class FindingUpdateView(FindingFilteredListMixin, UpdateView):
    model = Finding
    form_class = FindingForm
    template_name = "findings/finding_form.html"
    source = Finding.Source.AUTHORITY

    def get_queryset(self):
        return Finding.objects.filter(source=self.source)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": self.object.ref, "page_desc": self.object.title, "source": self.source})
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Finding saved.")
        return super().form_valid(form)


class FindingDeleteView(FindingFilteredListMixin, DeleteView):
    model = Finding
    template_name = "findings/finding_confirm_delete.html"
    source = Finding.Source.AUTHORITY

    def get_queryset(self):
        return Finding.objects.filter(source=self.source)

    def form_valid(self, form):
        messages.success(self.request, "Finding deleted.")
        return super().form_valid(form)
