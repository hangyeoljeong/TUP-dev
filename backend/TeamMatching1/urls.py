from django.urls import path
from . import views

urlpatterns = [
    path('api/teamup/input', views.save_user_input),
    path('api/teamup/apply', views.apply_teamup),
    path('api/teamup/matched', views.get_matched_teams),
    path('api/teamup/feedback', views.submit_feedback),
]
