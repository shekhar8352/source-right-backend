from django.urls import path

from . import api

urlpatterns = [
    path("live", api.live, name="health-live"),
    path("ready", api.ready, name="health-ready"),
]
