from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WaitingUser, Team, TeamMember, Feedback


# 1. 사용자 입력 저장
@api_view(['POST'])
def save_user_input(request):
    data = request.data
    user_id = data.get("userId")
    skills = data.get("skills", [])
    main_role = data.get("mainRole")
    sub_role = data.get("subRole")
    keywords = data.get("keywords", [])
    has_reward = data.get("hasReward", False)

    # 대기열에 사용자 추가 또는 갱신
    WaitingUser.objects.update_or_create(
        user_id=user_id,
        defaults={
            'skills': skills,
            'main_role': main_role,
            'sub_role': sub_role,
            'keywords': keywords,
            'has_reward': has_reward
        }
    )
    return Response({"message": "사용자 정보 저장 완료"}, status=200)


# 2. 팀 매칭 신청 + 리워드 우선 매칭
@api_view(['POST'])
def apply_teamup(request):
    user_id = request.data.get("userId")

    # 이미 팀에 속한 유저는 중복 매칭 방지
    if TeamMember.objects.filter(user_id=user_id).exists():
        return Response({"message": "이미 팀에 속한 유저입니다."}, status=400)

    try:
        current_user = WaitingUser.objects.get(user_id=user_id)
    except WaitingUser.DoesNotExist:
        return Response({"message": "대기열에 존재하지 않습니다."}, status=404)

    waiting_users = list(WaitingUser.objects.all())

    # 🎖️ 리워드 있는 사용자 우선 정렬
    waiting_users.sort(key=lambda u: (not u.has_reward, u.user_id != user_id))

    if len(waiting_users) < 4:
        return Response({"message": "인원이 부족합니다. 대기열에서 대기 중입니다."}, status=200)

    # 앞 4명으로 팀 구성
    team_members = waiting_users[:4]
    new_team = Team.objects.create(status="pending")

    for u in team_members:
        TeamMember.objects.create(team=new_team, user_id=u.user_id)
        u.delete()

    return Response({"message": "팀 매칭 완료", "teamId": new_team.id}, status=201)


# 3. 매칭된 팀 목록 조회
@api_view(['GET'])
def get_matched_teams(request):
    teams = Team.objects.prefetch_related('teammember_set').all()
    result = []

    for team in teams:
        members = [tm.user_id for tm in team.teammember_set.all()]
        result.append({
            "teamId": team.id,
            "members": members,
            "status": team.status
        })

    return Response(result, status=200)


# 4. 피드백 제출 및 재매칭 처리
@api_view(['POST'])
def submit_feedback(request):
    user_id = request.data.get("userId")
    team_id = request.data.get("teamId")
    agree = request.data.get("agree", True)

    Feedback.objects.update_or_create(
        user_id=user_id,
        team_id=team_id,
        defaults={"agree": agree}
    )

    feedbacks = Feedback.objects.filter(team_id=team_id)
    team_members = TeamMember.objects.filter(team_id=team_id)

    if feedbacks.count() == team_members.count():
        if all(f.agree for f in feedbacks):
            # 전원 동의 → 팀 확정
            Team.objects.filter(id=team_id).update(status="confirmed")
            return Response({"message": "모두 동의. 팀 확정 완료."}, status=200)
        else:
            # 일부 비동의 → 비동의자 재대기열로, 팀 해체
            disagreed_users = [f.user_id for f in feedbacks if not f.agree]
            for user_id in disagreed_users:
                # 예시: 기본값으로 재등록, 리워드 부여 가능
                WaitingUser.objects.create(user_id=user_id, has_reward=True)

            # 팀과 팀원 삭제
            Team.objects.filter(id=team_id).delete()
            TeamMember.objects.filter(team_id=team_id).delete()
            Feedback.objects.filter(team_id=team_id).delete()

            return Response({"message": "비동의 발생. 팀 해체 및 일부 사용자 재대기열 등록됨."}, status=200)

    return Response({"message": "피드백 저장 완료"}, status=201)
