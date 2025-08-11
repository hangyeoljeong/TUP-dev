from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from .models import Team, User, Application, Invitation
from .serializers import TeamSerializer, UserSerializer
from .models import UserProfile
from .serializers import InvitationSerializer


import json

# 1. 팀 생성
class TeamCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

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
        except ValueError:
            return Response({"error": "max_members는 숫자여야 합니다."}, status=400)

        tech = data.get('tech', [])
        looking_for = data.get('looking_for', [])

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

        try:
            team = Team.objects.create(
                name=name,
                leader=user_profile,
                tech=tech,
                looking_for=looking_for,
                max_members=max_members,
            )
            team.members.add(user_profile)

            return Response({
                'message': '팀 생성이 완료되었습니다.',
                'team_id': team.id
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

# 2. 유저 정보 수정
class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # UserProfile이 없으면 생성
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        data = request.data
        profile.skills = data.get('skills', profile.skills)
        profile.keywords = data.get('keywords', profile.keywords)
        profile.mainRole = data.get('mainRole', profile.mainRole)
        profile.subRole = data.get('subRole', profile.subRole)
        profile.save()

        return Response({
            'message': '유저 정보가 성공적으로 수정되었습니다.',
            'user_id': user.id
        }, status=200)
    
    
# 3. 팀 신청
class TeamApplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)
        user_profile = UserProfile.objects.get(user=request.user.userprofile)
        
        # 이미 신청했는지 중복 검사 (선택)
        if Application.objects.filter(team=team, user=user_profile).exists():
            return Response({"detail": "이미 신청한 팀입니다."}, status=400)

        Application.objects.create(team=team, user=user_profile)
        return Response({"detail": "팀 신청이 완료되었습니다."}, status=201)


# 4. 초대 수락
class AcceptInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_id):
        invitation = get_object_or_404(Invitation, id=invite_id)
        user_profile = UserProfile.objects.get(user=request.user.userprofile)

        if invitation.user != user_profile:
            return Response({"detail": "권한이 없습니다."}, status=403)

        invitation.status = 'accepted'
        invitation.save()

        # 팀 멤버로 추가
        invitation.team.members.add(user_profile)

        return Response({"detail": "초대가 수락되었습니다."})


# 5. 초대 거절
class RejectInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_id):
        invite = get_object_or_404(
            Invitation,
            id=invite_id,
            user=request.user.userprofile
        )

        # 상태 변경
        invite.status = 'rejected'
        invite.save()

        return Response({
            'message': f'팀 "{invite.team.id}" 초대를 거절했습니다.',
            'team_id': invite.team.id
        }, status=200)



# 6. 신청 수락
class AcceptApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        app = get_object_or_404(Application, id=application_id)

        # 권한 체크: 팀 리더만 가능
        if app.team.leader != request.user.userprofile:
            return Response({'error': '권한 없음'}, status=403)

        # 팀원 추가 및 상태 변경
        app.team.members.add(app.user)
        app.status = 'accepted'
        app.save()

        return Response({
            'message': f'"{app.user.username}"님의 신청을 수락했습니다.',
            'team_id': app.team.id
        }, status=200)



# 7. 신청 거절
class RejectApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        app = get_object_or_404(Application, id=application_id)

        # 권한 체크: 팀 리더만 가능
        if app.team.leader != request.user.userprofile:
            return Response({'error': '권한 없음'}, status=403)

        # 상태 변경
        app.status = 'rejected'
        app.save()

        return Response({
            'message': f'"{app.user.username}"님의 신청을 거절했습니다.',
            'team_id': app.team.id
        }, status=200)



# 8. 초대 보내기
class InviteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)

        # 권한 체크: 팀 리더만 가능
        if team.leader.user != request.user.userprofile:
            return Response({'error': '권한 없음'}, status=403)

        # 초대할 사용자 프로필 가져오기
        user_profile = get_object_or_404(UserProfile, user__id=request.data['user_id'])

        # 초대 생성
        Invitation.objects.create(team=team, user=user_profile, status='pending')

        return Response({
            'message': f'"{user_profile.user.username}"님에게 초대를 보냈습니다.',
            'team_id': team.id
        }, status=200)


# 9. 팀 리스트 (리워드 우선 정렬)
class TeamListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        teams = Team.objects.prefetch_related('members').select_related('leader').all()
        team_with_flags = []

        for team in teams:
            # 리더 또는 팀원 중 한 명이라도 리워드가 있는지 확인
            has_reward = team.leader.has_reward or any(m.has_reward for m in team.members.all())
            team_with_flags.append((has_reward, team))

        # 리워드 우선 정렬 (리워드 있는 팀이 먼저, 그 다음 ID 순)
        sorted_teams = sorted(team_with_flags, key=lambda x: (not x[0], x[1].id))
        sorted_team_objects = [t[1] for t in sorted_teams]

        serializer = TeamSerializer(sorted_team_objects, many=True)
        return Response({
            "message": "팀 목록을 리워드 우선으로 정렬하여 반환합니다.",
            "teams": serializer.data
        }, status=200)


# 10. 팀 상세
class TeamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, team_id):
        team = get_object_or_404(
            Team.objects.prefetch_related('members', 'application_set__user'),
            id=team_id
        )
        serializer = TeamSerializer(team)
        return Response(serializer.data)


# 11. 내 초대 내역
class MyInvitesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = request.user.userprofile  # UserProfile 인스턴스 가져오기
        invites = Invitation.objects.filter(user=user_profile, status='pending')
        serializer = InvitationSerializer(invites, many=True)
        return Response(serializer.data)


# 12. 내가 신청한 팀들
class MyApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        apps = Application.objects.filter(user=request.user.userprofile).select_related('team')
        data = [{'id': app.id, 'team': app.team.id, 'status': app.status} for app in apps]
        return Response(data)


# 13. 역할·기술·평점 필터링
class ApplicantFilterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.query_params.get('role', '')
        skill = request.query_params.get('skill', '')
        min_rating = request.query_params.get('min_rating', '')

        users = User.objects.all()

        if role:
            users = users.filter(mainRole__icontains=role)

        if skill:
            users = users.filter(skills__icontains=skill)

        if min_rating:
            try:
                min_rating = float(min_rating)
                users = users.filter(rating__gte=min_rating)
            except ValueError:
                pass

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
