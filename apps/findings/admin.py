from django.contrib import admin

from apps.findings.models import Finding


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ("seq", "source", "title", "device", "status", "cls", "due_date")
    list_filter = ("source", "status", "cls", "kind", "category")
    search_fields = ("title", "legacy_id", "authority")
