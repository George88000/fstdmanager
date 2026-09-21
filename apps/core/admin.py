from django.contrib import admin

from apps.core.models import OrganizationSettings


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(admin.ModelAdmin):
    list_display = ("ato_name", "threshold_days")
