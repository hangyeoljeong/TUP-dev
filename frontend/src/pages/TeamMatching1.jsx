// src/pages/TeamMatching1.jsx
import React, { useState, useEffect } from "react";
import MenuIcon from "@mui/icons-material/Menu";
import DrawerMenu from "../components/DrawerMenu";
import ContestModal from "../components/ContestModal";
import { calculateDday } from "../utils/dateUtils";
import "./TeamMatching1.css";
import {
  applyTeamup,
  getMatchedTeams,
  submitFeedback,
  getWaitingUsers, // ✅ 추가
} from "../api/teamup1";

// 공모전 목록 (그대로)
const contestList = [
  {
    id: 1,
    title: "2025 AWS x Codetree 프로그래밍 경진대회",
    description: "클라우드 환경에서의 문제 해결 프로그래밍",
    category: "프로그래밍, 클라우드",
    deadline: "2025-05-16",
    start: "2025-04-21",
    organizer: "AWS / 코드트리",
    image: "/aws.png",
  },
  {
    id: 2,
    title: "제7회 서울교육 데이터 분석·활용 아이디어 공모전",
    description: "교육 데이터를 활용한 분석 및 시각화",
    category: "데이터/코딩",
    deadline: "2025-06-01",
    start: "2025-04-21",
    organizer: "서울특별시교육청",
    image: "/seoul.png",
  },
  {
    id: 3,
    title: "2025년 경기도서관 크리에이티브 시너지 공모전",
    description: "공공도서관 시스템 개선 아이디어 공모",
    category: "IT기획/프로그래밍",
    deadline: "2025-06-30",
    start: "2025-04-09",
    organizer: "경기도 / 경기도서관",
    image: "/creative.png",
  },
  {
    id: 4,
    title: "2025 GH 공간복지 청년 공모전",
    description: "공간 기술 기반의 아이디어 및 프로토타입 공모",
    category: "공간IT/UX설계",
    deadline: "2025-06-29",
    start: "2025-06-02",
    organizer: "경기주택도시공사",
    image: "/gh.png",
  },
  {
    id: 5,
    title: "제6회 뉴스읽기 뉴스일기 공모전",
    description: "뉴스 데이터를 활용한 콘텐츠 기획",
    category: "미디어/코딩교육",
    deadline: "2025-07-31",
    start: "2025-04-07",
    organizer: "한국언론진흥재단",
    image: "/news.png",
  },
];

// 백엔드 응답 → UI에서 쓰는 형태로 정규화
const normalizeUsers = (rows = []) =>
  rows.map((u) => ({
    id: Number(u.userId) || u.id, // 필수
    name: u.name || `사용자 ${u.userId}`, // 스크린샷처럼 이름 표시
    mainRole: u.mainRole || "입력 없음",
    subRole: u.subRole || "입력 없음",
    keywords: Array.isArray(u.keywords) ? u.keywords : [],
    rating: typeof u.rating === "number" ? u.rating : undefined, // 없으면 "별점 없음" 노출
    participation:
      typeof u.participation === "number" ? u.participation : undefined,
  }));

function TeamMatching1() {
  const currentUser = { id: 99, name: "이명준", rating: 4.8, participation: 2 };

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [openMenus, setOpenMenus] = useState({});
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedContest, setSelectedContest] = useState(null);

  const [userSkills, setUserSkills] = useState([]); // (모달 입력)
  const [matchedUsers, setMatchedUsers] = useState([]); // [{teamId, members:[userId...], status}]
  const [feedbacks, setFeedbacks] = useState({});
  const [users, setUsers] = useState([]); // ✅ 대기열 (DB)
  const [loading, setLoading] = useState(true);

  // 1) 대기열 50명 로드
  useEffect(() => {
    (async () => {
      try {
        const data = await getWaitingUsers();
        setUsers(normalizeUsers(data)); // ← 필요 필드만
      } catch (e) {
        console.error("대기열 불러오기 실패:", e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // 2) 매칭된 팀 목록 로드
  useEffect(() => {
    (async () => {
      try {
        const data = await getMatchedTeams();
        setMatchedUsers(data);
      } catch (e) {
        console.error("팀 목록 로드 실패:", e);
      }
    })();
  }, []);

  // 3) 피드백 제출
  const onFeedback = async (targetUserId, vote) => {
    // 현재 내가 속한 팀 찾기 (API 구조: { teamId, members:[userId...] })
    const myTeam = matchedUsers.find(
      (t) => Array.isArray(t.members) && t.members.includes(currentUser.id)
    );
    const teamId = myTeam?.teamId;
    if (!teamId) return;

    if (feedbacks[targetUserId]) return; // 중복 제출 방지

    try {
      await submitFeedback({
        teamId,
        userId: targetUserId,
        agree: vote === "👍",
      });
      setFeedbacks((prev) => ({ ...prev, [targetUserId]: vote }));
    } catch (err) {
      console.error("피드백 제출 실패:", err);
    }
  };

  // 4) 팀 매칭 실행
  const handleMatchTeam = async () => {
    try {
      const res = await applyTeamup(currentUser.id);
      if (res?.teamId) {
        const teams = await getMatchedTeams();
        setMatchedUsers(teams);
      }
    } catch (e) {
      console.error("팀 매칭 오류:", e);
    }
  };

  return (
    <div className="team-matching-container">
      {/* 헤더 */}
      <header className="team-matching-header">
        <span className="logo">TUP!</span>
        {!drawerOpen && (
          <button
            className="menu-button"
            onClick={() => setDrawerOpen(true)}
            aria-label="메뉴 열기"
          >
            <MenuIcon style={{ fontSize: "2.2rem", color: "#FF6B35" }} />
          </button>
        )}
      </header>

      {/* 드로어 메뉴 */}
      <DrawerMenu
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        openMenus={openMenus}
        onToggle={setOpenMenus}
      />

      {/* 소개 문구 */}
      <div className="matching-intro">
        <h1>
          <span className="highlight">AutoTeamUp</span> - 빠르게 팀 결성하기
        </h1>
        <p>
          공모전을 선택한 참가자들이 랜덤으로 팀을 결성한 후,{" "}
          <strong>2차 피드백</strong>을 통해 최종 팀을 확정하는 방식입니다
        </p>
      </div>

      {/* 공모전 카드 리스트 */}
      <section className="contest-list-section">
        <h3 className="contest-section-title">
          📢 공모전을 찾아 팀업 진행하기
        </h3>
        <div className="contest-grid">
          {contestList.map((contest) => (
            <div
              key={contest.id}
              className="hover-card"
              onClick={() => {
                setSelectedContest(contest);
                setModalOpen(true);
              }}
            >
              <img src={contest.image} alt="공모전" className="hover-image" />
              <div className="hover-details">
                <h3>{contest.title}</h3>
                <p>
                  마감: {contest.deadline} ({calculateDday(contest.deadline)})
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 모달 */}
      {selectedContest && (
        <ContestModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          selectedContest={selectedContest}
          users={users} // ✅ DB 대기열
          setUsers={setUsers} // (모달 내 저장 시 업데이트)
          userSkills={userSkills}
          setUserSkills={setUserSkills}
          matched={matchedUsers}
          matchTeam={handleMatchTeam}
          feedbacks={feedbacks}
          onFeedback={onFeedback} // ✅ submitFeedback 연동
          currentUser={currentUser}
          loading={loading}
        />
      )}
    </div>
  );
}

export default TeamMatching1;
