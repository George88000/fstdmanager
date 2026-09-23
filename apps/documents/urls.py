from django.urls import path

from apps.documents.views import (
    DocumentCreateView,
    DocumentDeleteView,
    DocumentMoveView,
    FolderCreateView,
    FolderDeleteView,
    FolderDetailView,
    FolderListView,
)

app_name = "documents"

urlpatterns = [
    path("", FolderListView.as_view(), name="list"),
    path("folders/add/", FolderCreateView.as_view(), name="folder_add"),
    path("folders/<int:pk>/", FolderDetailView.as_view(), name="folder"),
    path("folders/<int:pk>/delete/", FolderDeleteView.as_view(), name="folder_delete"),
    path("upload/", DocumentCreateView.as_view(), name="upload"),
    path("<int:pk>/move/", DocumentMoveView.as_view(), name="move"),
    path("<int:pk>/delete/", DocumentDeleteView.as_view(), name="delete"),
]
