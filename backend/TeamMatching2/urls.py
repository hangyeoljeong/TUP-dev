# TeamMatching2/urls.py
from django.urls import path
from .views import (
    TeamCreateView,
    UserProfileUpdateView,
    TeamApplyView,
    AcceptInviteView,
    RejectInviteView,
    AcceptApplicationView,
    RejectApplicationView,
    InviteUserView,
    TeamListView,
    TeamDetailView,
    MyInvitesView,
    MyApplicationsView,
    ApplicantFilterView,
)

app_name = "team_matching2"

urlpatterns = [
    # 팀 목록/생성/상세
    path("teams/", TeamListView.as_view(), name="team-list"),
    path("teams/create/", TeamCreateView.as_view(), name="team-create"),
    path("teams/<int:team_id>/", TeamDetailView.as_view(), name="team-detail"),

    # 팀에 지원 / 사용자 초대
    path("teams/<int:team_id>/apply/", TeamApplyView.as_view(), name="team-apply"),
    path("teams/<int:team_id>/invite/", InviteUserView.as_view(), name="invite-user"),

    # 초대 수락/거절
    path("invites/<int:invite_id>/accept/", AcceptInviteView.as_view(), name="invite-accept"),
    path("invites/<int:invite_id>/reject/", RejectInviteView.as_view(), name="invite-reject"),

    # 신청 수락/거절 (리더 전용)
    path("applications/<int:application_id>/accept/", AcceptApplicationView.as_view(), name="application-accept"),
    path("applications/<int:application_id>/reject/", RejectApplicationView.as_view(), name="application-reject"),

    # 내 초대/신청 조회
    path("me/invites/", MyInvitesView.as_view(), name="my-invites"),
    path("me/applications/", MyApplicationsView.as_view(), name="my-applications"),

    # 내 프로필 수정
    path("users/me/", UserProfileUpdateView.as_view(), name="userprofile-update"),

    # 지원자 필터
    path("applicants/filter/", ApplicantFilterView.as_view(), name="applicant-filter"),
]
