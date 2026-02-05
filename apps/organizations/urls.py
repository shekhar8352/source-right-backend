from django.urls import path

from . import api

urlpatterns = [
    path("organizations", api.create_organization_view, name="create-organization"),
    path("organizations/invites", api.invite_user_view, name="invite-organization-user"),
    path(
        "organizations/invites/accept",
        api.accept_invite_view,
        name="accept-organization-invite",
    ),
]
