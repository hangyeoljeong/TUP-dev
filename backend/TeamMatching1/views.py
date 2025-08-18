from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from dbapp.models import WaitingUser, Team, TeamMember, Feedback

@api_view(['POST'])
def save_user_input(request):
    d = request.data
    user_id = str(d.get("userId","")).strip()
    if not user_id: return Response({"message":"userId가 필요합니다."}, 400)
    WaitingUser.objects.update_or_create(
        user_id=user_id,
        defaults={
            "skills": d.get("skills",[]) or [],
            "main_role": d.get("mainRole") or "unknown",
            "sub_role": d.get("subRole"),
            "keywords": d.get("keywords",[]) or [],
            "has_reward": bool(d.get("hasReward", False)),
        },
    )
    return Response({"message":"사용자 정보 저장 완료"}, 200)

@api_view(['POST'])
def apply_teamup(request):
    raw = request.data.get("userId")
    if raw is None: return Response({"message":"userId가 필요합니다."}, 400)
    try: user_pk = int(str(raw).strip())
    except ValueError: return Response({"message":"userId는 정수여야 합니다."}, 400)

    if TeamMember.objects.filter(user_id=user_pk).exists():
        return Response({"message":"이미 팀에 속한 유저입니다."}, 400)

    try: WaitingUser.objects.get(user_id=str(user_pk))
    except WaitingUser.DoesNotExist:
        return Response({"message":"대기열에 존재하지 않습니다."}, 404)

    waiting = list(WaitingUser.objects.all())
    waiting.sort(key=lambda w: (not bool(w.has_reward), w.user_id != str(user_pk)))
    if len(waiting) < 4:
        return Response({"message":"인원이 부족합니다. 대기열에서 대기 중입니다."}, 200)

    selected = waiting[:4]
    if not str(selected[0].user_id).isdigit():
        return Response({"message":"대기열 user_id가 숫자가 아닙니다."}, 400)
    leader_pk = int(selected[0].user_id)

    with transaction.atomic():
        new_team = Team.objects.create(
            name=None, leader_id=leader_pk, matching_type='auto', is_finalized=False
        )
        for idx, w in enumerate(selected):
            TeamMember.objects.create(
                team_id=new_team.id,
                user_id=int(w.user_id),
                role='leader' if idx==0 else 'member',
            )
            w.delete()
    return Response({"message":"팀 매칭 완료","teamId":new_team.id}, 201)

@api_view(['GET'])
def get_matched_teams(request):
    teams = Team.objects.prefetch_related('teammember_set').all()
    return Response([{
        "teamId": t.id,
        "members": [tm.user_id for tm in t.teammember_set.all()],
        "status": "confirmed" if t.is_finalized else "pending",
    } for t in teams], 200)

@api_view(['POST'])
def submit_feedback(request):
    team_id = request.data.get("teamId")
    raw = request.data.get("userId")
    agree = bool(request.data.get("agree", True))
    if team_id is None or raw is None: return Response({"message":"teamId, userId가 필요합니다."}, 400)
    try: user_pk = int(str(raw).strip())
    except ValueError: return Response({"message":"userId는 정수여야 합니다."}, 400)

    Feedback.objects.update_or_create(
        team_id=team_id, user_id=user_pk, defaults={"is_agree": agree}
    )
    fbs = list(Feedback.objects.filter(team_id=team_id))
    cnt = TeamMember.objects.filter(team_id=team_id).count()

    if len(fbs)==cnt:
        if all(f.is_agree for f in fbs):
            Team.objects.filter(id=team_id).update(is_finalized=True)
            return Response({"message":"모두 동의. 팀 확정 완료."}, 200)
        else:
            from django.db import transaction
            with transaction.atomic():
                TeamMember.objects.filter(team_id=team_id).delete()
                Feedback.objects.filter(team_id=team_id).delete()
                Team.objects.filter(id=team_id).delete()
            return Response({"message":"비동의 발생. 팀 해체 완료."}, 200)
    return Response({"message":"피드백 저장 완료"}, 201)
