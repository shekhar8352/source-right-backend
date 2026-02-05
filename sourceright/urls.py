from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", include("apps.healthcheck.urls")),
    path("api/", include("apps.core.urls")),
    path("api/", include("apps.organizations.urls")),
]
