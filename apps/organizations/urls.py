from django.urls import path

from . import api

urlpatterns = [
    path("organizations", api.create_organization_view, name="create-organization"),
    path("organizations/users", api.list_organization_users_view, name="list-organization-users"),
    path(
        "organizations/users/<int:user_id>/deactivate",
        api.deactivate_organization_user_view,
        name="deactivate-organization-user",
    ),
    path(
        "organizations/users/<int:user_id>/reactivate",
        api.reactivate_organization_user_view,
        name="reactivate-organization-user",
    ),
    path("organizations/invites", api.invite_user_view, name="invite-organization-user"),
    path(
        "organizations/invites/accept",
        api.accept_invite_view,
        name="accept-organization-invite",
    ),
]
