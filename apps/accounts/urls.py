from django.urls import path

from . import api

urlpatterns = [
    path("accounts/register", api.register_user_view, name="accounts-register"),
]
