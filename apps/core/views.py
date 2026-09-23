from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from apps.core.forms import CategoryForm, SettingsForm
from apps.core.models import OrganizationSettings
from apps.core.utils import (
    build_compliance_alerts,
    clear_list_filters,
    compliance_badge,
    dashboard_chart_data,
    dashboard_stat_cards,
    remember_list_filters,
    remembered_list_url,
)


class RemembersListFiltersMixin:
    def get(self, request, *args, **kwargs):
        url_name = request.resolver_match.view_name
        if request.GET:
            remember_list_filters(request, url_name)
        else:
            clear_list_filters(request, url_name)
        return super().get(request, *args, **kwargs)


class ReturnsToFilteredListMixin:
    list_url_name = None

    def get_list_url_name(self) -> str:
        if not self.list_url_name:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} must define list_url_name or get_list_url_name()."
            )
        return self.list_url_name

    def get_success_url(self):
        return remembered_list_url(self.request, self.get_list_url_name())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = remembered_list_url(self.request, self.get_list_url_name())
        return context


class DashboardView(TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = OrganizationSettings.get_solo()
        threshold = org.threshold_days
        compliance_items = build_compliance_alerts(threshold)
        charts = dashboard_chart_data()

        context.update(
            {
                "page_title": "Dashboard",
                "page_desc": "Live overview of your FSTD compliance and training records",
                "stat_cards": dashboard_stat_cards(threshold),
                "compliance_items": compliance_items[:20],
                "compliance_badge": compliance_badge(compliance_items),
                "threshold": threshold,
                **charts,
            }
        )
        return context


class SettingsView(FormView):
    template_name = "core/settings.html"
    form_class = SettingsForm
    success_url = reverse_lazy("core:settings")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = OrganizationSettings.get_solo()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings_obj = OrganizationSettings.get_solo()
        context.update(
            {
                "page_title": "Settings",
                "page_desc": "ATO details and finding categories",
                "category_form": CategoryForm(),
                "categories": settings_obj.finding_categories or [],
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        settings_obj = OrganizationSettings.get_solo()
        if action == "add_category":
            form = CategoryForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data["new_category"].strip()
                categories = list(settings_obj.finding_categories or [])
                if name and name not in categories:
                    categories.append(name)
                    settings_obj.finding_categories = categories
                    settings_obj.save()
                    messages.success(request, f'Category "{name}" added.')
                else:
                    messages.error(request, "Category already exists or is empty.")
            return redirect("core:settings")
        if action == "remove_category":
            name = request.POST.get("category", "").strip()
            categories = [c for c in (settings_obj.finding_categories or []) if c != name]
            settings_obj.finding_categories = categories
            settings_obj.save()
            messages.success(request, f'Category "{name}" removed.')
            return redirect("core:settings")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Settings saved.")
        return super().form_valid(form)
