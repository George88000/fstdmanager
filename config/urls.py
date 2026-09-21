from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path("devices/", include("apps.devices.urls")),
    path("", include("apps.qualification.urls")),
    path("findings/", include("apps.findings.urls")),
    path("", include("apps.operations.urls")),
    path("documents/", include("apps.documents.urls")),
    path("remote/", include("apps.remote.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
