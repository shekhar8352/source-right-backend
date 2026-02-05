from django.urls import path

from . import api

urlpatterns = [
    path("organizations", api.create_organization_view, name="create-organization"),
    path("example", api.example_view, name="core-example"),
]
