import random
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import User, Team, TeamMember, WaitingUser, Feedback, TeamAvoid

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

        # 🚫 TeamAvoid 기반으로 '다시 만나면 안 되는 관계' 반영
        from .models import TeamAvoid  # 함수 맨 위 import 추가해도 됨

        # 모든 회피 관계 불러오기
        avoid_pairs = TeamAvoid.objects.all()
        avoid_dict = {}
        for pair in avoid_pairs:
            avoid_dict.setdefault(pair.user_a, set()).add(pair.user_b)

        # ✅ 2️⃣ 4명씩 잘라서 팀 구성 (랜덤 순서 유지)
        teams_to_create = []
        used_users = set()

        while len(available_users) >= TEAM_SIZE:
            selected_users = []
            for u in available_users:
                # 회피 관계 있는 사람과 팀 구성 금지
                if any(u.id in avoid_dict.get(sel.id, set()) for sel in selected_users):
                    continue
                selected_users.append(u)
                if len(selected_users) == TEAM_SIZE:
                    break

            if len(selected_users) < TEAM_SIZE:
                break  # 남은 인원은 회피 관계 때문에 팀 구성 불가

            new_team = Team.objects.create(status="pending")

            for u in selected_users:
                TeamMember.objects.create(
                    team=new_team,
                    user_id=u.id
                )
                matched_user_ids.append(u.id)
                used_users.add(u.id)

            created_team_ids.append(new_team.id)

            # 이미 매칭된 인원 제거
            available_users = [u for u in available_users if u.id not in used_users]

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
    print("🔥 [Django] feedback 요청 도착!")
    print("📦 request.data:", request.data)
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
    print("🔥 [submit_feedback] 요청 도착:", request.method)
    print("📦 [submit_feedback] DATA:", request.data)

    data = request.data
    team_id = data.get("team_id") or data.get("teamId")
    user_id = data.get("user_id") or data.get("userId")
    agree = data.get("agree")

    agree = str(agree).lower() in ("true", "1", "yes", "y")

    # ✅ 필수값 검증
    if not team_id or not user_id:
        return Response({"message": "team_id, user_id가 필요합니다."}, status=400)

    try:
        team_id = int(team_id)
        user_pk = int(user_id)
    except ValueError:
        return Response({"message": "team_id, user_id는 정수여야 합니다."}, status=400)

    # ✅ 피드백 저장 (단순 저장만)
    Feedback.objects.update_or_create(
        team_id=team_id,
        user_id=user_pk,
        defaults={"agree": agree},
    )

    members_qs = TeamMember.objects.filter(team_id=team_id)
    cnt_members = members_qs.count()
    fbs = list(Feedback.objects.filter(team_id=team_id))

    # 아직 모두 완료 안됨 → 단순 저장
    if len(fbs) < cnt_members:
        return Response({"message": "피드백 저장 완료"}, status=201)

    # 모두 동의 → 팀 확정
    if all(f.agree for f in fbs):
        Team.objects.filter(id=team_id).update(is_finalized=True)
        return Response({"message": "모두 동의. 팀 확정 완료."}, status=200)

    # ✅ (수정됨) 여기서는 아무것도 이동시키지 않음.
    # 단순히 "피드백 모두 완료됨"만 알려줌
    disagree_ids = [f.user_id for f in fbs if not f.agree]
    return Response({
        "message": f"피드백 완료. 비동의 {len(disagree_ids)}명 있음.",
        "teamId": team_id,
        "disagreed_users": disagree_ids,
    }, status=200)


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

@csrf_exempt
@api_view(['POST'])
def apply_team_rematch(request):
    """
    👍 인원 유지, 👎 인원은 여기서 대기열 복귀 + 팀 재구성
    """
    data = request.data
    team_id = data.get("team_id") or data.get("teamId")
    agreed_user_ids = data.get("agreed_user_ids") or data.get("agreedUserIds")

    if not team_id or not agreed_user_ids:
        return Response({"message": "team_id 또는 agreed_user_ids가 필요합니다."}, status=400)

    team_id = int(team_id)
    agreed_user_ids = [int(uid) for uid in agreed_user_ids]

    team = get_object_or_404(Team, id=team_id)

    # ✅ 1️⃣ 피드백 중 비동의자 추출
    all_feedbacks = Feedback.objects.filter(team_id=team_id)
    disagree_ids = [f.user_id for f in all_feedbacks if not f.agree]

    # ✅ 2️⃣ 비동의자 대기열 복귀 처리
    def _rehydrate_defaults(uid: int):
        try:
            u = User.objects.get(id=uid)
            return {
                "skills": u.skills or [],
                "main_role": u.main_role or "unknown",
                "sub_role": u.sub_role,
                "keywords": u.keywords or [],
                "has_reward": bool(getattr(u, "has_reward", False)),
            }
        except User.DoesNotExist:
            return {
                "skills": [],
                "main_role": "unknown",
                "sub_role": None,
                "keywords": [],
                "has_reward": False,
            }

    with transaction.atomic():
        # ⚙️ 기존 팀 초기화
        TeamMember.objects.filter(team_id=team_id).delete()

        # 👎 비동의자 대기열 복귀
        for uid in disagree_ids:
            WaitingUser.objects.update_or_create(user_id=uid, defaults=_rehydrate_defaults(uid))

        # 👍 동의자 다시 팀에 추가
        for uid in agreed_user_ids:
            TeamMember.objects.create(team_id=team_id, user_id=uid)

        # ⚙️ 대기열에서 부족 인원 보충
        need = max(0, TEAM_SIZE - len(agreed_user_ids))
        waiting_candidates = list(WaitingUser.objects.exclude(user_id__in=agreed_user_ids))
        random.shuffle(waiting_candidates)

        new_members = list(agreed_user_ids)
        for w in waiting_candidates[:need]:
            TeamMember.objects.create(team_id=team_id, user_id=w.user_id)
            new_members.append(w.user_id)
            w.delete()  # ⚠️ 보충된 인원은 대기열에서 제거

        # 피드백 초기화 + 팀 미확정 상태로 설정
        Feedback.objects.filter(team_id=team_id).delete()
        Team.objects.filter(id=team_id).update(is_finalized=False)

    return Response({
        "message": f"재매칭 완료. 비동의자 {len(disagree_ids)}명 대기열 복귀 완료. 팀 {team_id} 재구성 완료.",
        "team_id": team_id,
        "new_members": new_members,
        "waiting_users_count": WaitingUser.objects.count(),
    }, status=200)

@csrf_exempt
@api_view(['POST'])
def move_disagreed_users_to_waiting(request):
    """
    피드백 결과 기반 팀 재조정 로직
    --------------------------------------------------
    1️⃣ 요청자가 '동의자'이면 → 팀 해체 + 전원 대기열 복귀
    2️⃣ 일부 '비동의자'만 있으면 → 비동의자 대기열 이동 + 대기열에서 새 인원으로 보충
    3️⃣ 전원 비동의이면 → 팀 해체 + 전원 대기열 복귀
    --------------------------------------------------
    """
    data = request.data
    team_id = data.get("team_id") or data.get("teamId")
    requester_id = data.get("user_id") or data.get("userId")

    if not team_id or not requester_id:
        return Response({"message": "team_id, user_id가 필요합니다."}, status=400)

    team_id = int(team_id)
    requester_id = int(requester_id)

    feedbacks = Feedback.objects.filter(team_id=team_id)
    team_members = list(TeamMember.objects.filter(team_id=team_id).values_list("user_id", flat=True))

    if not team_members:
        return Response({"message": "팀 멤버가 존재하지 않습니다."}, status=404)

    my_feedback = feedbacks.filter(user_id=requester_id).first()
    if not my_feedback:
        return Response({"message": "요청자의 피드백 정보를 찾을 수 없습니다."}, status=404)

    disagreed_user_ids = [f.user_id for f in feedbacks if not f.agree]
    agreed_user_ids = [f.user_id for f in feedbacks if f.agree]

    def _rehydrate(uid):
        """대기열 복귀 시 WaitingUser 필드 채움"""
        try:
            u = User.objects.get(id=uid)
            return {
                "skills": u.skills or [],
                "main_role": u.main_role or "unknown",
                "sub_role": u.sub_role,
                "keywords": u.keywords or [],
                "has_reward": bool(getattr(u, "has_reward", False)),
            }
        except User.DoesNotExist:
            return {
                "skills": [],
                "main_role": "unknown",
                "sub_role": None,
                "keywords": [],
                "has_reward": False,
            }

    with transaction.atomic():
        # ✅ Case 1: 요청자가 동의자 → 팀 해체 + 전원 대기열 복귀
        if my_feedback.agree:
            print(f"⚠️ [TEAM BREAK] 동의자 {requester_id} 요청으로 팀 {team_id} 해체")
            for uid in team_members:
                WaitingUser.objects.update_or_create(user_id=uid, defaults=_rehydrate(uid))
            TeamMember.objects.filter(team_id=team_id).delete()
            Team.objects.filter(id=team_id).delete()
            Feedback.objects.filter(team_id=team_id).delete()
            return Response({
                "message": f"동의자 {requester_id} 요청으로 팀 해체 및 전원 대기열 복귀 완료",
                "team_id": team_id,
                "requeued_users": team_members,
                "auto_teamup": False,
            }, status=200)

        # ✅ Case 2: 전원 비동의 → 팀 해체 + 전원 대기열 복귀
        if len(disagreed_user_ids) == len(team_members):
            print(f"❌ [TEAM BREAK] 전원 비동의 → 팀 {team_id} 해체")
            for uid in team_members:
                WaitingUser.objects.update_or_create(user_id=uid, defaults=_rehydrate(uid))
            TeamMember.objects.filter(team_id=team_id).delete()
            Team.objects.filter(id=team_id).delete()
            Feedback.objects.filter(team_id=team_id).delete()
            return Response({
                "message": "전원 비동의 → 팀 해체 및 전원 대기열 복귀 완료",
                "team_id": team_id,
                "requeued_users": team_members,
                "auto_teamup": False,
            }, status=200)

        # ✅ Case 3: 일부 비동의 → 비동의자만 대기열로 이동 + 대기열 인원으로 보충
        print(f"⚙️ [PARTIAL REMATCH] 팀 {team_id}: 일부 비동의자 {disagreed_user_ids} 이동 처리 중...")

        # 비동의자 → 대기열 복귀
        for uid in disagreed_user_ids:
            WaitingUser.objects.update_or_create(user_id=uid, defaults=_rehydrate(uid))

        # 팀에서 비동의자 제거
        TeamMember.objects.filter(team_id=team_id, user_id__in=disagreed_user_ids).delete()

        # 보충 인원 계산
        remaining_count = TeamMember.objects.filter(team_id=team_id).count()
        need = max(0, TEAM_SIZE - remaining_count)

        if need > 0:
            # 대기열에서 보충 인원 선택
            candidates = list(
                WaitingUser.objects.exclude(user_id__in=agreed_user_ids + disagreed_user_ids)[:need]
            )
            for candidate in candidates:
                TeamMember.objects.create(team_id=team_id, user_id=candidate.user_id)
                candidate.delete()  # 대기열에서 제거
            print(f"🧩 팀 {team_id} → {need}명 보충 완료")

        new_members = list(
            TeamMember.objects.filter(team_id=team_id).values_list("user_id", flat=True)
        )

        return Response({
            "message": f"비동의자 {len(disagreed_user_ids)}명 대기열 이동 + {need}명 보충 완료",
            "team_id": team_id,
            "new_members": new_members,
            "requeued_users": disagreed_user_ids,
            "auto_teamup": True
        }, status=200)
    
@csrf_exempt
@api_view(['POST'])
def reset_demo_data(request):
    print("🚀 reset_demo_data 호출됨")

    try:
        with transaction.atomic():
            # ✅ 1️⃣ 기존 데이터 싹 비우기
            print("🧹 Team, TeamMember, Feedback, WaitingUser 데이터 삭제 중...")
            Team.objects.all().delete()
            TeamMember.objects.all().delete()
            Feedback.objects.all().delete()
            WaitingUser.objects.all().delete()

            print("✅ 모든 데이터 삭제 완료")

            # ✅ 2️⃣ User 테이블은 유지하되, 데모용 대기열 새로 채움
            existing_users = list(User.objects.all())
            if not existing_users:
                print("⚠️ User 테이블이 비어있음 → 가짜 유저 생성")
                for i in range(1, 51):
                    User.objects.create(
                        id=i,
                        name=f"DemoUser{i}",
                        main_role=random.choice(["개발", "기획", "디자인"]),
                        sub_role=random.choice(["보조", "PM", "QA"]),
                        skills=random.sample(["Python", "React", "Figma", "SQL", "Node"], 2),
                        keywords=random.sample(["AI", "데이터", "웹", "UX", "핀테크"], 2),
                        rating=round(random.uniform(3.0, 5.0), 1),
                        participation=random.randint(1, 10),
                    )
                existing_users = list(User.objects.all())

            # ✅ 3️⃣ 대기열 다시 채우기 (50명 제한)
            sample_users = random.sample(existing_users, min(50, len(existing_users)))
            for u in sample_users:
                WaitingUser.objects.create(
                    user_id=u.id,
                    skills=u.skills or [],
                    main_role=u.main_role or "개발",
                    sub_role=u.sub_role or "디자인",
                    keywords=u.keywords or [],
                    has_reward=False,
                )

        print("✅ Demo 데이터 및 대기열 완전 초기화 완료")
        return Response({"message": "Demo 데이터 및 대기열 완전 초기화 완료!"}, status=200)

    except Exception as e:
        print("❌ reset_demo_data 오류:", e)
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)