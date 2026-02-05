from django.urls import path

from . import api

urlpatterns = [
    path("example", api.example_view, name="core-example"),
]
