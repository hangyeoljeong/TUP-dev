from django.urls import path
from . import views

urlpatterns = [
    path("ping/", views.ping, name="dbapp-ping"),
    path("users/", views.users, name="dbapp-users"),
]
