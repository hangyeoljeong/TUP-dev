# backend/api/tm2/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Prefetch

from ..models import Team, UserProfile, Application, Invitation
from ..serializers import (
    TeamSerializer, UserSerializer, UserProfileSerializer, InvitationSerializer
)

import json


# ---------- 내부 유틸 ----------
def _member_count(team: Team) -> int:
    return team.members.count()

def _is_leader(team: Team, user_profile: UserProfile) -> bool:
    return team.leader_id == user_profile.id

def _already_member(team: Team, user_profile: UserProfile) -> bool:
    return team.members.filter(id=user_profile.id).exists()

def _team_is_full(team: Team) -> bool:
    return _member_count(team) >= int(team.max_members or 0)


# 1) 팀 생성
class TeamCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data

        # 현재 로그인한 사용자의 프로필
        try:
            user_profile = request.user.userprofile
        except Exception as e:
            return Response({"error": f"UserProfile error: {str(e)}"}, status=400)

        name = data.get('name')
        if not name:
            return Response({"error": "팀 이름(name)은 필수입니다."}, status=400)

        max_members = data.get('max_members')
        if max_members is None:
            return Response({"error": "max_members는 필수입니다."}, status=400)
        try:
            max_members = int(max_members)
            if max_members < 1:
                return Response({"error": "max_members는 1 이상이어야 합니다."}, status=400)
        except ValueError:
            return Response({"error": "max_members는 숫자여야 합니다."}, status=400)

        tech = data.get('tech', [])
        looking_for = data.get('looking_for', [])

        # 문자열로 들어와도 JSON 파싱 시도
        if isinstance(tech, str):
            try:
                tech = json.loads(tech)
            except Exception:
                tech = []
        if isinstance(looking_for, str):
            try:
                looking_for = json.loads(looking_for)
            except Exception:
                looking_for = []

        # 팀 생성 및 리더를 멤버에 추가
        team = Team.objects.create(
            name=name,
            leader=user_profile,
            tech=tech,
            looking_for=looking_for,
            max_members=max_members,
            status='open',
        )
        team.members.add(user_profile)  # 리더 포함
        return Response({"message": "팀 생성이 완료되었습니다.", "team_id": team.id}, status=201)


# 2) 유저 프로필 수정
class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        profile, _created = UserProfile.objects.get_or_create(user=user)

        d = request.data
        profile.skills = d.get('skills', profile.skills)
        profile.keywords = d.get('keywords', profile.keywords)
        profile.mainRole = d.get('mainRole', profile.mainRole)
        profile.subRole = d.get('subRole', profile.subRole)
        # rating/participation/has_reward 등은 별도 정책으로 갱신
        profile.save()

        return Response({"message": "유저 정보가 성공적으로 수정되었습니다.", "user_id": user.id}, status=200)


# 3) 팀 신청 (유저 → 팀)
class TeamApplyView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)

        # 현재 사용자 프로필
        try:
            user_profile = request.user.userprofile
        except Exception:
            return Response({"detail": "UserProfile이 필요합니다."}, status=400)

        if _already_member(team, user_profile):
            return Response({"detail": "이미 팀원입니다."}, status=400)

        if _team_is_full(team):
            return Response({"detail": "정원이 가득 찬 팀입니다."}, status=400)

        # 중복 신청 방지
        if Application.objects.filter(team=team, user=user_profile, status='pending').exists():
            return Response({"detail": "대기 중인 신청이 이미 있습니다."}, status=400)

        Application.objects.create(team=team, user=user_profile, status='pending')
        return Response({"detail": "팀 신청이 완료되었습니다."}, status=201)


# 4) 초대 수락
class AcceptInviteView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, invite_id):
        # 현재 사용자 프로필
        try:
            user_profile = request.user.userprofile
        except Exception:
            return Response({"detail": "UserProfile이 필요합니다."}, status=400)

        invitation = get_object_or_404(Invitation.objects.select_for_update(), id=invite_id)

        if invitation.user_id != user_profile.id:
            return Response({"detail": "권한이 없습니다."}, status=403)
        if invitation.status != 'pending':
            return Response({"detail": "이미 처리된 초대입니다."}, status=400)

        team = invitation.team
        if _team_is_full(team):
            invitation.status = 'rejected'
            invitation.save()
            return Response({"detail": "정원 초과로 수락할 수 없습니다."}, status=400)

        if _already_member(team, user_profile):
            invitation.status = 'accepted'
            invitation.save()
            return Response({"detail": "이미 팀원입니다."}, status=200)

        # 팀 합류
        team.members.add(user_profile)
        invitation.status = 'accepted'
        invitation.save()

        # 정원 꽉 차면 상태 닫기(선택)
        if _team_is_full(team):
            team.status = 'closed'
            team.save(update_fields=['status'])

        return Response({"detail": "초대를 수락했습니다.", "team_id": team.id}, status=200)


# 5) 초대 거절
class RejectInviteView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, invite_id):
        try:
            user_profile = request.user.userprofile
        except Exception:
            return Response({"detail": "UserProfile이 필요합니다."}, status=400)

        invite = get_object_or_404(Invitation.objects.select_for_update(), id=invite_id)
        if invite.user_id != user_profile.id:
            return Response({"detail": "권한이 없습니다."}, status=403)

        if invite.status != 'pending':
            return Response({"detail": "이미 처리된 초대입니다."}, status=400)

        invite.status = 'rejected'
        invite.save()
        return Response({"message": f'팀 "{invite.team.id}" 초대를 거절했습니다.', "team_id": invite.team.id}, status=200)


# 6) 신청 수락 (팀 리더만)
class AcceptApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, application_id):
        app = get_object_or_404(Application.objects.select_for_update(), id=application_id)
        team = app.team

        try:
            me = request.user.userprofile
        except Exception:
            return Response({'error': 'UserProfile이 필요합니다.'}, status=400)

        if not _is_leader(team, me):
            return Response({'error': '권한 없음'}, status=403)
        if app.status != 'pending':
            return Response({'error': '이미 처리된 신청입니다.'}, status=400)

        if _team_is_full(team):
            app.status = 'rejected'
            app.save()
            return Response({'error': '정원 초과로 수락 불가'}, status=400)

        if _already_member(team, app.user):
            app.status = 'accepted'
            app.save()
            username = getattr(getattr(app.user, 'user', None), 'username', str(app.user.id))
            return Response({'message': f'"{username}"님은 이미 팀원입니다.' , 'team_id': team.id}, status=200)

        team.members.add(app.user)
        app.status = 'accepted'
        app.save()

        if _team_is_full(team):
            team.status = 'closed'
            team.save(update_fields=['status'])

        username = getattr(getattr(app.user, 'user', None), 'username', str(app.user.id))
        return Response({'message': f'"{username}"님의 신청을 수락했습니다.', 'team_id': team.id}, status=200)


# 7) 신청 거절 (팀 리더만)
class RejectApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, application_id):
        app = get_object_or_404(Application.objects.select_for_update(), id=application_id)
        team = app.team

        try:
            me = request.user.userprofile
        except Exception:
            return Response({'error': 'UserProfile이 필요합니다.'}, status=400)

        if not _is_leader(team, me):
            return Response({'error': '권한 없음'}, status=403)

        if app.status != 'pending':
            return Response({'error': '이미 처리된 신청입니다.'}, status=400)

        app.status = 'rejected'
        app.save()
        username = getattr(getattr(app.user, 'user', None), 'username', str(app.user.id))
        return Response({'message': f'"{username}"님의 신청을 거절했습니다.', 'team_id': team.id}, status=200)


# 8) 초대 보내기 (팀 리더만)
class InviteUserView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)

        try:
            me = request.user.userprofile
        except Exception:
            return Response({'error': 'UserProfile이 필요합니다.'}, status=400)

        # 리더 권한 체크 (같은 타입 비교)
        if not _is_leader(team, me):
            return Response({'error': '권한 없음'}, status=403)

        if _team_is_full(team):
            return Response({'error': '정원 초과 팀입니다.'}, status=400)

        # 초대 대상 (Django User.id가 아닌 UserProfile.user.id를 기대)
        target_user_id = request.data.get('user_id')
        if target_user_id is None:
            return Response({'error': 'user_id(초대 대상 Django User.id)가 필요합니다.'}, status=400)

        # 대상 UserProfile 찾기
        target_profile = get_object_or_404(UserProfile, user__id=target_user_id)

        if _already_member(team, target_profile):
            return Response({'error': '이미 팀원입니다.'}, status=400)

        # 중복 초대 방지
        if Invitation.objects.filter(team=team, user=target_profile, status='pending').exists():
            return Response({'error': '대기 중인 초대가 이미 있습니다.'}, status=400)

        Invitation.objects.create(team=team, user=target_profile, status='pending')
        username = getattr(getattr(target_profile, 'user', None), 'username', str(target_profile.id))
        return Response({'message': f'"{username}"님에게 초대를 보냈습니다.', 'team_id': team.id}, status=200)


# 9) 팀 리스트 (리워드 우선 정렬, 기본: open 우선 표시)
class TeamListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Team.objects.select_related('leader').prefetch_related('members')
        # 상태 필터 옵션: ?status=open/closed
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        team_with_flags = []
        for team in qs:
            has_reward = getattr(team.leader, 'has_reward', False) or any(
                getattr(m, 'has_reward', False) for m in team.members.all()
            )
            team_with_flags.append((has_reward, team))

        sorted_teams = [t for _, t in sorted(team_with_flags, key=lambda x: (not x[0], x[1].id))]
        data = TeamSerializer(sorted_teams, many=True).data
        return Response({"message": "리워드 우선으로 정렬된 팀 목록입니다.", "teams": data}, status=200)


# 10) 팀 상세
class TeamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, team_id):
        team = get_object_or_404(
            Team.objects.select_related('leader').prefetch_related('members', 'application_set__user', 'invitation_set__user'),
            id=team_id
        )
        return Response(TeamSerializer(team).data, status=200)


# 11) 내 초대 내역 (받은 초대 - 기본 pending)
class MyInvitesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_profile = request.user.userprofile
        except Exception:
            return Response({"detail": "UserProfile이 필요합니다."}, status=400)

        status_param = request.query_params.get('status', 'pending')
        invites = Invitation.objects.filter(user=user_profile)
        if status_param:
            invites = invites.filter(status=status_param)

        # 현재 InvitationSerializer는 (id, user, status)만 포함 → 필요 시 커스터마이즈 가능
        return Response(InvitationSerializer(invites.order_by('-id'), many=True).data, status=200)


# 12) 내가 신청한 팀들
class MyApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_profile = request.user.userprofile
        except Exception:
            return Response({"detail": "UserProfile이 필요합니다."}, status=400)

        apps = Application.objects.select_related('team').filter(user=user_profile).order_by('-id')
        data = [{'id': a.id, 'team': a.team.id, 'status': a.status} for a in apps]
        return Response(data, status=200)


# 13) 지원자 필터 (역할/기술/평점)
class ApplicantFilterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.query_params.get('role', '')
        skill = request.query_params.get('skill', '')
        min_rating = request.query_params.get('min_rating', '')

        qs = UserProfile.objects.select_related('user').all()

        if role:
            qs = qs.filter(mainRole__icontains=role) | qs.filter(subRole__icontains=role)

        if skill:
            # JSONField 텍스트 검색(백엔드 DB에 따라 contains 동작 상이 → 호환성 위해 icontains)
            qs = qs.filter(skills__icontains=skill)

        if min_rating:
            try:
                qs = qs.filter(rating__gte=float(min_rating))
            except ValueError:
                pass

        # 필요 시 is_leader/has_reward 같은 태그 필터도 확장 가능
        data = UserProfileSerializer(qs.order_by('-rating', 'id'), many=True).data
        return Response(data, status=200)
