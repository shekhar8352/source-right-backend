from django.urls import path

from . import api

urlpatterns = [
    path("accounts/register", api.register_user_view, name="accounts-register"),
    path("accounts/login", api.login_view, name="accounts-login"),
    path("accounts/token/refresh", api.RefreshTokenView.as_view(), name="accounts-token-refresh"),
    path("accounts/logout", api.logout_view, name="accounts-logout"),
]
