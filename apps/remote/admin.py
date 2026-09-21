from django.contrib import admin

from apps.remote.models import RemoteConnection


@admin.register(RemoteConnection)
class RemoteConnectionAdmin(admin.ModelAdmin):
    list_display = ("label", "anydesk_id")
    filter_horizontal = ("devices",)
