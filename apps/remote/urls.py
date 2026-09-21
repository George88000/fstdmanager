from django.urls import path

from apps.remote.views import RemoteCreateView, RemoteDeleteView, RemoteListView, RemoteUpdateView

app_name = "remote"

urlpatterns = [
    path("", RemoteListView.as_view(), name="list"),
    path("add/", RemoteCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", RemoteUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", RemoteDeleteView.as_view(), name="delete"),
]
