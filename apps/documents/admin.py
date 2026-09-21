from django.contrib import admin

from apps.documents.models import Document, Folder


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "is_standard")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "folder", "device", "uploaded_on", "size")
    list_filter = ("folder",)
