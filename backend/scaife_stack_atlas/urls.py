from django.urls import include, path, re_path

from django.contrib import admin

from . import views
from .tocs.views import serve_toc, tocs_index


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("scaife_viewer.atlas.urls")),
    path("tocs/<filename>", serve_toc, name="serve_toc"),
    path("tocs/", tocs_index, name="tocs_index"),
    re_path(r"^", views.FrontendAppView.as_view()),
]
