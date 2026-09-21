from django.contrib import admin

from apps.qualification.models import (
    NavdataEvent,
    NavdataRecord,
    QualificationCycle,
    QualificationEvent,
)


class QualificationEventInline(admin.TabularInline):
    model = QualificationEvent
    extra = 0


@admin.register(QualificationCycle)
class QualificationCycleAdmin(admin.ModelAdmin):
    list_display = ("device", "kind", "last_completed", "next_due")
    list_filter = ("kind",)
    inlines = [QualificationEventInline]


class NavdataEventInline(admin.TabularInline):
    model = NavdataEvent
    extra = 0


@admin.register(NavdataRecord)
class NavdataRecordAdmin(admin.ModelAdmin):
    list_display = ("device", "last_updated", "cycle_ref")
    inlines = [NavdataEventInline]
