from django.urls import path

from apps.findings.models import Finding
from apps.findings.views import (
    FindingArchiveView,
    FindingCreateView,
    FindingDeleteView,
    FindingInfoView,
    FindingListView,
    FindingUpdateView,
)

app_name = "findings"

urlpatterns = [
    path("", FindingListView.as_view(source=Finding.Source.AUTHORITY), name="authority"),
    path("add/", FindingCreateView.as_view(source=Finding.Source.AUTHORITY), name="authority_add"),
    path("<int:pk>/info/", FindingInfoView.as_view(source=Finding.Source.AUTHORITY), name="authority_info"),
    path("<int:pk>/edit/", FindingUpdateView.as_view(source=Finding.Source.AUTHORITY), name="authority_edit"),
    path("<int:pk>/delete/", FindingDeleteView.as_view(source=Finding.Source.AUTHORITY), name="authority_delete"),
    path("<int:pk>/archive/", FindingArchiveView.as_view(source=Finding.Source.AUTHORITY), name="authority_archive"),
    path("internal/", FindingListView.as_view(source=Finding.Source.INTERNAL), name="internal"),
    path("internal/add/", FindingCreateView.as_view(source=Finding.Source.INTERNAL), name="internal_add"),
    path(
        "internal/<int:pk>/info/",
        FindingInfoView.as_view(source=Finding.Source.INTERNAL),
        name="internal_info",
    ),
    path(
        "internal/<int:pk>/edit/",
        FindingUpdateView.as_view(source=Finding.Source.INTERNAL),
        name="internal_edit",
    ),
    path(
        "internal/<int:pk>/delete/",
        FindingDeleteView.as_view(source=Finding.Source.INTERNAL),
        name="internal_delete",
    ),
    path(
        "internal/<int:pk>/archive/",
        FindingArchiveView.as_view(source=Finding.Source.INTERNAL),
        name="internal_archive",
    ),
]
