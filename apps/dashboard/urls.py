from django.urls import path

from . import api

urlpatterns = [
    path("dashboard/me", api.me_view, name="dashboard-me"),
]
