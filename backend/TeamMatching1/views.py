import random
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import User, Team, TeamMember, WaitingUser, Feedback

# 팀 정원
TEAM_SIZE = 4

@csrf_exempt
@api_view(['POST'])
def save_user_input(request):
    d = request.data
    user_id = str(d.get("userId", "")).strip()
    if not user_id:
        return Response({"message": "userId가 필요합니다."}, status=400)\
        
    try:
        existing_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        existing_user = None

    # ✅ 기존 name을 유지하고, 새 name이 주어졌을 때만 업데이트
    new_name = d.get("name")
    if not new_name or new_name.strip() == "":
        name_value = existing_user.name if existing_user else "이름없음"
    else:
        name_value = new_name.strip()

    # ✅ rating/participation 기존 값 유지
    rating_value = (
        d.get("rating")
        if d.get("rating") is not None
        else (existing_user.rating if existing_user else 0)
    )
    participation_value = (
        d.get("participation")
        if d.get("participation") is not None
        else (existing_user.participation if existing_user else 0)
    )

    # ✅ User 테이블에는 기본 정보만 저장
    User.objects.update_or_create(
        id=user_id,
        defaults={
            "name": name_value,
            "main_role": (
                d.get("mainRole").strip()
                if d.get("mainRole") and d.get("mainRole").strip() != ""
                else (existing_user.main_role if existing_user else "unknown")
            ),
            "sub_role": (
                d.get("subRole").strip()
                if d.get("subRole") and d.get("subRole").strip() != ""
                else (existing_user.sub_role if existing_user else None)
            ),
            "keywords": (
                d.get("keywords")
                if d.get("keywords")
                else (existing_user.keywords if existing_user else [])
            ),
            "skills": (
                d.get("skills")
                if d.get("skills")
                else (existing_user.skills if existing_user else [])
            ),
            "rating": rating_value,
            "participation": participation_value,
        },
    )

    # ✅ WaitingUser 테이블에는 매칭용 데이터 저장
    WaitingUser.objects.update_or_create(
        user_id=user_id,
        defaults={
            "skills": (
                d.get("skills")
                if d.get("skills")
                else (existing_user.skills if existing_user else [])
            ),
            "main_role": (
                d.get("mainRole").strip()
                if d.get("mainRole") and d.get("mainRole").strip() != ""
                else (existing_user.main_role if existing_user else "unknown")
            ),
            "sub_role": (
                d.get("subRole").strip()
                if d.get("subRole") and d.get("subRole").strip() != ""
                else (existing_user.sub_role if existing_user else None)
            ),
            "keywords": (
                d.get("keywords")
                if d.get("keywords")
                else (existing_user.keywords if existing_user else [])
            ),
            "has_reward": bool(d.get("hasReward", False)),
        },
    )

    return Response({"message": f"user {user_id} 저장 완료"}, status=200)



@csrf_exempt
@api_view(['POST'])
def apply_teamup(request):
    print("🔥 [views.py] apply_teamup 요청 도착!", request.method)
    print("📦 [RAW BODY]:", request.body)
    print("📦 [DATA PARSED]:", request.data)
    print("📦 [HEADERS]:", request.headers)

    raw = request.data.get("userId")
    if raw is None:
        return Response({"message": "userId가 필요합니다.", "debug": request.data}, status=400)

    try:
        user_pk = int(str(raw).strip())
    except ValueError:
        return Response({"message": "userId는 정수여야 합니다.", "debug": raw}, status=400)
    
    print(f"✅ userId 정상 파싱됨: {user_pk}")

    # 이미 팀에 소속된 경우 예외 처리
    if TeamMember.objects.filter(user_id=user_pk).exists():
        return Response({"message": "이미 팀에 속한 유저입니다."}, status=400)

    # 현재 DB에 존재하는 유저인지 확인
    try:
        applicant = User.objects.get(id=user_pk)
    except User.DoesNotExist:
        return Response({"message": "해당 유저를 찾을 수 없습니다."}, status=404)

    # 아직 팀에 소속되지 않은 모든 유저 불러오기
    available_users = list(User.objects.exclude(
        id__in=TeamMember.objects.values_list("user_id", flat=True)
    ))

    # ✅ 1️⃣ 신청자는 반드시 포함시키고, 나머지는 랜덤하게 섞기
    import random
    random.shuffle(available_users)  # 순서 무작위화
    # 신청자(user_pk)를 맨 앞으로 이동시켜 팀이 반드시 포함되게
    available_users.sort(key=lambda u: (u.id != user_pk))

    with transaction.atomic():
        created_team_ids = []
        matched_user_ids = [] 

        # ✅ 2️⃣ 4명씩 잘라서 팀 구성 (랜덤 순서 유지)
        while len(available_users) >= TEAM_SIZE:
            selected_users = available_users[:TEAM_SIZE]
            available_users = available_users[TEAM_SIZE:]

            new_team = Team.objects.create(status="pending")

            for u in selected_users:
                TeamMember.objects.create(
                    team=new_team,
                    user_id=u.id
                )
                matched_user_ids.append(u.id)
                
            created_team_ids.append(new_team.id)

        # ✅ 여기서 한 번에 대기열 삭제
        if matched_user_ids:
            WaitingUser.objects.filter(user_id__in=matched_user_ids).delete()

        # ✅ 3️⃣ 남은 인원이 4명 미만이면 대기열로 이동
        for u in available_users:
            WaitingUser.objects.update_or_create(
                user_id=u.id,
                defaults={
                    "skills": [],
                    "main_role": u.main_role,
                    "sub_role": u.sub_role,
                    "keywords": u.keywords,
                    "has_reward": False,
                }
            )

    # ✅ 4️⃣ 응답 데이터 구성 (기존 로직 유지)
    teams_data = []
    for tid in created_team_ids:
        team = Team.objects.get(id=tid)
        members = []
        for tm in TeamMember.objects.filter(team=team):
            try:
                u = User.objects.get(id=tm.user_id)
                waiting_info = WaitingUser.objects.filter(user_id=u.id).first()
                members.append({
                    "id": u.id,
                    "name": u.name,
                    "mainRole": waiting_info.main_role if waiting_info and waiting_info.main_role else u.main_role,
                    "subRole": waiting_info.sub_role if waiting_info and waiting_info.sub_role else u.sub_role,
                    "keywords": waiting_info.keywords if waiting_info and waiting_info.keywords else u.keywords,
                    "skills": waiting_info.skills if waiting_info else [],
                    "rating": u.rating,
                    "participation": u.participation,
                })
            except User.DoesNotExist:
                members.append({"id": tm.user_id, "name": "알 수 없음"})
        teams_data.append({
            "teamId": team.id,
            "members": members,
            "status": team.status,
        })

    if teams_data:
        return Response({
            "message": f"{len(created_team_ids)}개 팀 매칭 완료",
            "teams": teams_data
        }, status=201)
    else:
        return Response({"message": "인원이 부족합니다. 대기열에 등록되었습니다."}, status=200)


@csrf_exempt
@api_view(['GET'])
def get_matched_teams(request):
    teams = Team.objects.prefetch_related('teammember_set').all()
    result = []

    for t in teams:
        members = []
        for tm in t.teammember_set.all():
            try:
                u = User.objects.get(id=tm.user_id)
                w = WaitingUser.objects.filter(user_id=tm.user_id).first()

                members.append({
                    "id": u.id,
                    "name": u.name,
                    "mainRole": w.main_role if w else u.main_role,
                    "subRole": w.sub_role if w else u.sub_role,
                    "skills": (w.skills if w else []),
                    "keywords": (w.keywords if w else u.keywords),
                    "rating": u.rating,
                    "participation": u.participation,
                })
            except User.DoesNotExist:
                members.append({
                    "id": tm.user_id,
                    "name": f"User {tm.user_id}",
                })
        result.append({
            "teamId": t.id,
            "members": members,
            "status": "confirmed" if t.is_finalized else "pending",
        })

    return Response(result, status=200)

@csrf_exempt
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

        # 3) 리더가 나갔으면 새 리더 선임(남은 팀원 중 user_id가 가장 작은 사람) -> db 무결성 때문에 하나 무조건 정해야댐
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
# ✅ 추가할 코드 (TeamMatching1/views.py 맨 아래에 넣어줘)


@csrf_exempt
@api_view(['GET'])
def get_waiting_users(request):
    """
    WaitingUser 테이블의 현재 사용자 목록을 반환
    - 초기에는 이명준(99) 제외 50명 생성
    - 이후에는 그대로 유지 (제한 없음)
    - 이명준이 있으면 유지, 없으면 제외
    """
    import random

    # ✅ 현재 WaitingUser 불러오기 (99 제외)
    waiting_users = list(WaitingUser.objects.exclude(user_id=99))

    # ✅ 초기 시드 생성 (대기열이 비어 있을 때만)
    if not waiting_users:
        users = list(
            User.objects.exclude(id=99)
                        .exclude(name__isnull=True)
                        .exclude(name__exact="")
                        .exclude(name__icontains="undefined")
        )

        if not users:
            return Response({"waiting_users": []})

        random_users = random.sample(users, min(50, len(users)))
        waiting_instances = [
            WaitingUser(
                user_id=u.id,
                main_role=u.main_role,
                sub_role=u.sub_role,
                skills=u.skills,
                keywords=u.keywords,
                has_reward=False,   
            )
            for u in random_users
        ]
        WaitingUser.objects.bulk_create(waiting_instances)
        waiting_users = WaitingUser.objects.exclude(user_id=99)

        # ✅ 이 시점에만 순서 랜덤화
        random.shuffle(waiting_users)

    # ✅ 응답 데이터 구성
    data = []
    for w in waiting_users:
        try:
            u = User.objects.get(id=w.user_id)
            if not u.name or u.name.strip() == "" or u.name.lower() == "undefined":
                continue
            data.append({
                "id": u.id,
                "name": u.name,
                "mainRole": w.main_role or u.main_role or "",
                "subRole": w.sub_role or u.sub_role or "",
                "keywords": w.keywords or u.keywords or [],
                "rating": u.rating,
                "participation": u.participation,
            })
        except User.DoesNotExist:
            continue

    # ✅ 만약 이명준이 대기열에 추가되어 있다면 항상 포함
    try:
        mj_user = User.objects.get(id=99)
        if WaitingUser.objects.filter(user_id=99).exists():
            data.append({
                "id": mj_user.id,
                "name": mj_user.name,
                "main_role": mj_user.main_role,
                "sub_role": mj_user.sub_role,
                "keywords": mj_user.keywords,
                "rating": mj_user.rating,
                "participation": mj_user.participation,
            })
    except User.DoesNotExist:
        pass

    unique = list({item["id"]: item for item in data}.values())
    return Response({"waiting_users": unique})

