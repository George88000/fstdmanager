from django.contrib import admin

from apps.devices.models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "level", "serial", "location", "maintenance_program")
    search_fields = ("name", "serial", "manufacturer", "legacy_id")
    list_filter = ("type", "level", "maintenance_program")
