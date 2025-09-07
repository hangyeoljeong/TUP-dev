"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views.
"""
from django.contrib import admin
from django.urls import path, include
# JWT를 쓸 거면 아래 두 줄 주석 해제 + simplejwt 설치
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # TM1 (자동매칭) — 별도 앱
    path('api/tm1/', include('TeamMatching1.urls')),

    # TM2 (초대/지원) — api 서브라우터에서 관리 (api/urls.py -> api/tm2/urls.py)
    path('api/', include('api.urls')),

    # JWT 엔드포인트 (선택)
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
