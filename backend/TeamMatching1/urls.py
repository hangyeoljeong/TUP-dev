from django.urls import path
from . import views

app_name = "team_matching1"

urlpatterns = [
    path("save/", views.save_user_input),
    path("apply/", views.apply_teamup),
    path("teams/", views.get_matched_teams),
    path("feedback/", views.submit_feedback),
    path("waiting/", views.get_waiting_users),
    
    # path("teamup/submit_feedback", views.perform_feedback_action),  # ✔️ 마지막 API만 /teamup 사용
]
