from django.urls import path

from apps.devices.views import DeviceCreateView, DeviceDeleteView, DeviceListView, DeviceUpdateView

app_name = "devices"

urlpatterns = [
    path("", DeviceListView.as_view(), name="list"),
    path("add/", DeviceCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", DeviceUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", DeviceDeleteView.as_view(), name="delete"),
]
