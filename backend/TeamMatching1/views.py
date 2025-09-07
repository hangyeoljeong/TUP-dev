# backend/TeamMatching1/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from dbapp.models import WaitingUser, Team, TeamMember, Feedback

# 팀 정원(기존 TM1 로직 기준 4명)
TEAM_SIZE = 4

@api_view(['POST'])
def save_user_input(request):
    d = request.data
    user_id = str(d.get("userId","")).strip()
    if not user_id:
        return Response({"message":"userId가 필요합니다."}, status=400)

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
    return Response({"message":"사용자 정보 저장 완료"}, status=200)

@api_view(['POST'])
def apply_teamup(request):
    raw = request.data.get("userId")
    if raw is None:
        return Response({"message":"userId가 필요합니다."}, status=400)
    try:
        user_pk = int(str(raw).strip())
    except ValueError:
        return Response({"message":"userId는 정수여야 합니다."}, status=400)

    if TeamMember.objects.filter(user_id=user_pk).exists():
        return Response({"message":"이미 팀에 속한 유저입니다."}, status=400)

    try:
        WaitingUser.objects.get(user_id=str(user_pk))
    except WaitingUser.DoesNotExist:
        return Response({"message":"대기열에 존재하지 않습니다."}, status=404)

    waiting = list(WaitingUser.objects.all())
    # 리워드 보유자 우선, 그리고 신청자 가깝게
    waiting.sort(key=lambda w: (not bool(w.has_reward), w.user_id != str(user_pk)))
    if len(waiting) < TEAM_SIZE:
        return Response({"message":"인원이 부족합니다. 대기열에서 대기 중입니다."}, status=200)

    selected = waiting[:TEAM_SIZE]
    if not str(selected[0].user_id).isdigit():
        return Response({"message":"대기열 user_id가 숫자가 아닙니다."}, status=400)
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

    return Response({"message":"팀 매칭 완료","teamId":new_team.id}, status=201)

@api_view(['GET'])
def get_matched_teams(request):
    teams = Team.objects.prefetch_related('teammember_set').all()
    return Response([{
        "teamId": t.id,
        "members": [tm.user_id for tm in t.teammember_set.all()],
        "status": "confirmed" if t.is_finalized else "pending",
    } for t in teams], status=200)

@api_view(['POST'])
def submit_feedback(request):
    team_id = request.data.get("teamId")
    raw = request.data.get("userId")
    agree = bool(request.data.get("agree", True))
    if team_id is None or raw is None:
        return Response({"message":"teamId, userId가 필요합니다."}, status=400)
    try:
        user_pk = int(str(raw).strip())
    except ValueError:
        return Response({"message":"userId는 정수여야 합니다."}, status=400)

    # 피드백 저장/갱신
    Feedback.objects.update_or_create(
        team_id=team_id, user_id=user_pk, defaults={"is_agree": agree}
    )

    # 현재 팀 구성원 수와 피드백 수 비교
    members_qs = TeamMember.objects.filter(team_id=team_id)
    cnt_members = members_qs.count()
    fbs = list(Feedback.objects.filter(team_id=team_id))
    if len(fbs) < cnt_members:
        return Response({"message":"피드백 저장 완료"}, status=201)

    # 전원 제출됨
    if all(f.is_agree for f in fbs):
        Team.objects.filter(id=team_id).update(is_finalized=True)
        return Response({"message":"모두 동의. 팀 확정 완료."}, status=200)

    # 일부 비동의 → 비동의자만 팀 이탈 + 대기열 복귀 + 결원 자동보충(4명까지)
    disagree_ids = [f.user_id for f in fbs if not f.is_agree]

    # 가능한 경우 api.UserProfile에서 WaitingUser 기본값 복구
    def _rehydrate_defaults(uid: int):
        try:
            from api.models import UserProfile
            up = UserProfile.objects.get(user__id=uid)
            return {
                "skills": up.skills or [],
                "main_role": getattr(up, "mainRole", None) or "unknown",
                "sub_role": getattr(up, "subRole", None),
                "keywords": up.keywords or [],
                "has_reward": bool(getattr(up, "has_reward", False)),
            }
        except Exception:
            return {
                "skills": [],
                "main_role": "unknown",
                "sub_role": None,
                "keywords": [],
                "has_reward": False,
            }

    with transaction.atomic():
        team = Team.objects.select_for_update().get(id=team_id)

        # 1) 비동의자만 팀에서 제거 + 대기열 복귀
        removed_leader = False
        for uid in disagree_ids:
            # 팀원 제거
            TeamMember.objects.filter(team_id=team_id, user_id=uid).delete()
            if team.leader_id == uid:
                removed_leader = True
            # 대기열 복귀(정보 복구)
            WaitingUser.objects.update_or_create(
                user_id=str(uid),
                defaults=_rehydrate_defaults(uid),
            )

        # 2) 남은 팀원이 없으면 팀 해체
        remaining = list(TeamMember.objects.filter(team_id=team_id).order_by('user_id'))
        if not remaining:
            Feedback.objects.filter(team_id=team_id).delete()
            Team.objects.filter(id=team_id).delete()
            return Response({"message": f"모두 비동의로 팀 해체. 비동의 {len(disagree_ids)}명 대기열 복귀 완료."}, status=200)

        # 3) 리더가 나갔으면 새 리더 선임(남은 팀원 중 user_id가 가장 작은 사람)
        if removed_leader:
            new_leader_id = remaining[0].user_id
            Team.objects.filter(id=team_id).update(leader_id=new_leader_id)

        # 4) 결원 자동 보충 (정원 TEAM_SIZE까지)
        current_cnt = len(remaining)
        need = max(0, TEAM_SIZE - current_cnt)
        if need > 0:
            # 방금 팀에서 나간 비동의자들은 같은 라운드에서 재합류하지 않도록 제외
            exclude_ids = set(str(x) for x in disagree_ids)
            waiting = list(WaitingUser.objects.exclude(user_id__in=exclude_ids))
            # 리워드 우선, 그다음 user_id 오름차순
            waiting.sort(key=lambda w: (not bool(w.has_reward), int(w.user_id) if str(w.user_id).isdigit() else 1_000_000))
            take = waiting[:need]
            for w in take:
                # 중복 방지
                if not TeamMember.objects.filter(team_id=team_id, user_id=int(w.user_id)).exists():
                    TeamMember.objects.create(team_id=team_id, user_id=int(w.user_id), role='member')
                    w.delete()
            # 인원 재확인
            current_cnt = TeamMember.objects.filter(team_id=team_id).count()

        # 팀은 아직 확정 아님(재동의 필요 가능성) → 기존 피드백은 리셋
        Team.objects.filter(id=team_id).update(is_finalized=False)
        Feedback.objects.filter(team_id=team_id).delete()

        # 현재 멤버 목록 반환
        members = list(TeamMember.objects.filter(team_id=team_id).values_list('user_id', flat=True))
        return Response({
            "message": f"비동의 {len(disagree_ids)}명 팀 이탈 및 대기열 복귀. 현재 팀원 {current_cnt}명, 정원 {TEAM_SIZE}명.",
            "teamId": team_id,
            "members": members
        }, status=200)
