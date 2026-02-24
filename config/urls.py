"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", RedirectView.as_view(url="/admin/login/", permanent=False)),
    path("", include("utility.urls")),
    path("transmedia/", include("transmedia.urls")),
]
