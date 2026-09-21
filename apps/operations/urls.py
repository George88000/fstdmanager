from django.urls import path

from apps.operations.views import (
    HoldItemCreateView,
    HoldItemDeleteView,
    HoldItemInfoView,
    HoldItemListView,
    HoldItemUpdateView,
    MaintenanceListView,
    MaintenanceUpdateView,
    PermanentDefectCreateView,
    PermanentDefectDeleteView,
    PermanentDefectInfoView,
    PermanentDefectListView,
    PermanentDefectUpdateView,
)

app_name = "operations"

urlpatterns = [
    path("hold-items/", HoldItemListView.as_view(), name="hold_items"),
    path("hold-items/add/", HoldItemCreateView.as_view(), name="hold_item_add"),
    path("hold-items/<int:pk>/info/", HoldItemInfoView.as_view(), name="hold_item_info"),
    path("hold-items/<int:pk>/edit/", HoldItemUpdateView.as_view(), name="hold_item_edit"),
    path("hold-items/<int:pk>/delete/", HoldItemDeleteView.as_view(), name="hold_item_delete"),
    path("permanent-defects/", PermanentDefectListView.as_view(), name="permanent_defects"),
    path("permanent-defects/add/", PermanentDefectCreateView.as_view(), name="permanent_defect_add"),
    path(
        "permanent-defects/<int:pk>/info/",
        PermanentDefectInfoView.as_view(),
        name="permanent_defect_info",
    ),
    path(
        "permanent-defects/<int:pk>/edit/",
        PermanentDefectUpdateView.as_view(),
        name="permanent_defect_edit",
    ),
    path(
        "permanent-defects/<int:pk>/delete/",
        PermanentDefectDeleteView.as_view(),
        name="permanent_defect_delete",
    ),
    path("maintenance/", MaintenanceListView.as_view(), name="maintenance"),
    path("maintenance/<int:pk>/", MaintenanceUpdateView.as_view(), name="maintenance_edit"),
]
