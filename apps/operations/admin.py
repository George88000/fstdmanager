from django.contrib import admin

from apps.operations.models import HoldItem, MaintenanceEvent, MaintenanceTask, PermanentDefect


@admin.register(HoldItem)
class HoldItemAdmin(admin.ModelAdmin):
    list_display = ("seq", "device", "defect_category", "report_date", "due_date", "closure_date", "closed_at", "archived_at")
    list_filter = ("defect_category",)


@admin.register(PermanentDefect)
class PermanentDefectAdmin(admin.ModelAdmin):
    list_display = ("seq", "device", "title", "category", "date_noted")


class MaintenanceEventInline(admin.TabularInline):
    model = MaintenanceEvent
    extra = 0


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ("device", "task_key", "last_completed", "next_due")
    inlines = [MaintenanceEventInline]
