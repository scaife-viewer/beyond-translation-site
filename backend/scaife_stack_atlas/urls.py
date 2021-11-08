from django.urls import include, path, re_path

from django.contrib import admin

from . import views
from .chs_homer_proxy.views import proxy_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("scaife_viewer.atlas.urls")),
    path(r"homer-chs-proxy/graphql/", proxy_view),
    re_path(r"^", views.FrontendAppView.as_view()),
]
