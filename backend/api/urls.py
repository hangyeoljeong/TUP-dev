# backend/api/urls.py
from django.urls import path, include
from .views import APIRootView, HealthCheckView, ServerTimeView, WhoAmIView

urlpatterns = [
    path("", APIRootView.as_view(), name="api-root"),
    path("health/", HealthCheckView.as_view(), name="api-health"),
    path("server-time/", ServerTimeView.as_view(), name="api-server-time"),
    path("whoami/", WhoAmIView.as_view(), name="api-whoami"),

    # 매칭 앱들 네임스페이스 묶기
    path("team1/", include("TeamMatching1.urls")),
    path("team2/", include("TeamMatching2.urls")),
]
