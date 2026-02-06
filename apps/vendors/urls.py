from django.urls import path

from . import api

urlpatterns = [
    path("internal/vendors", api.create_vendor_view, name="create-vendor"),
]
