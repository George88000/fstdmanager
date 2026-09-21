from django.urls import path

from apps.qualification.models import QualificationCycle
from apps.qualification.views import CycleListView, CycleUpdateView, NavdataListView, NavdataUpdateView

app_name = "qualification"

urlpatterns = [
    path("qtg/", CycleListView.as_view(kind=QualificationCycle.Kind.QTG), name="qtg"),
    path(
        "qtg/<int:device_id>/",
        CycleUpdateView.as_view(kind=QualificationCycle.Kind.QTG),
        name="qtg_edit",
    ),
    path(
        "subjective/",
        CycleListView.as_view(kind=QualificationCycle.Kind.SUBJECTIVE),
        name="subjective",
    ),
    path(
        "subjective/<int:device_id>/",
        CycleUpdateView.as_view(kind=QualificationCycle.Kind.SUBJECTIVE),
        name="subjective_edit",
    ),
    path("navdata/", NavdataListView.as_view(), name="navdata"),
    path("navdata/<int:device_id>/", NavdataUpdateView.as_view(), name="navdata_edit"),
]
