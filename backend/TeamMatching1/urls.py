from django.urls import path
from . import views

urlpatterns = [
    path('save', views.save_user_input),
    path('apply', views.apply_teamup),
    path('teams', views.get_matched_teams),
    path('feedback', views.submit_feedback),
]
