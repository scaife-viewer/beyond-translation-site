from django.urls import include, path, re_path

from django.contrib import admin

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("scaife_viewer.atlas.urls")),
    re_path(r"^", views.FrontendAppView.as_view()),
]
