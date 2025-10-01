import React, { useState, useEffect } from "react";
import MenuIcon from "@mui/icons-material/Menu";
import tupImg from "./tup_img.png";
import "./TeamMatching2.css";
import { useNavigate } from "react-router-dom";
import DrawerMenu from "../components/DrawerMenu";
import { toast } from "react-toastify";
import {
  createTeam,
  getTeamList,
  acceptApplicant,
  // ↓ 아래 함수들은 이후 단계에서 쓰일 수 있으니 미리 주석만 추가해둠
  applyToTeam,
  rejectApplicant,
  sendInvite,
  respondToInvite,
  getApplicants,
  updateUserProfile,
   deleteTeam,
   deregisterProfile
   ,
} from "../api/teamup2";


const allSkills = [
  "리더십",
  "기획력",
  "소통",
  "협업",
  "꼼꼼함",
  "책임감",
  "창의력",
  "분석력",
  "논리력",
  "실행력",
  "시간관리",
  "문제해결",
  "열정",
  "끈기",
  "적응력",
  "발표력",
  "공감력",
  "전략적 사고",
  "자기주도성",
];

// 더미팀 목록
const baseTeams = [
  {
    id: 1,
    leader: { name: "김민수", user: { username: "김민수" } },
    skills: ["React", "Node.js"],
    looking_for: ["디자이너", "기획자"],
    category: "웹/앱 서비스 개발",
    status: "모집중",
    max_members: 4,
    intro: "열정 가득한 팀장입니다.",
    // ★★★ members 배열에 leader 정보를 추가합니다 ★★★
    members: [{ user: { username: "김민수" }, mainRole: "PM" }],
  },
  {
    id: 2,
    leader: { name: "서지훈", user: { username: "서지훈" } },
    skills: ["Java", "Spring"],
    looking_for: ["프론트엔드 엔지니어"],
    category: "공공데이터 활용 서비스 개발",
    status: "모집중",
    max_members: 3,
    intro: "함께 성장할 분을 찾습니다.",
    // ★★★ members 배열에 leader 정보를 추가합니다 ★★★
    members: [{ user: { username: "서지훈" }, mainRole: "백엔드 개발" }],
  },
  {
    id: 3,
    leader: { name: "박영희", user: { username: "박영희" } },
    skills: ["Flutter", "Firebase"],
    looking_for: ["백엔드 개발자"],
    category: "데이터베이스 관련 운용",
    status: "모집완료",
    max_members: 5,
    intro: "저와 함께 성장해요!",
    members: [
      { user: { username: "박영희" }, mainRole: "DB 구축" },
      { user: { username: "팀원A" }, mainRole: "프론트엔드 개발" },
      { user: { username: "팀원B" }, mainRole: "백엔드 개발" },
      { user: { username: "팀원C" }, mainRole: "디자이너" },
      { user: { username: "팀원D" }, mainRole: "기획자" },
    ],
  },
];

// 더미 팀원 목록
const baseApplicants = [
  {
    id: 101,
    user: { username: "나개발" },
    skills: ["React", "TypeScript", "GraphQL"],
    keywords: ["꼼꼼함", "책임감", "소통"],
    mainRole: "프론트엔드 개발자",
    subRole: "UI/UX 디자이너",
    rating: 4.8,
    participation: 5,
    intro: "사용자 경험을 중요시하는 프론트엔드 개발자입니다."
  },
  {
    id: 102,
    user: { username: "박기획" },
    skills: ["Figma", "Notion", "Jira"],
    keywords: ["기획력", "분석력", "리더십"],
    mainRole: "PM",
    subRole: "서비스 기획자",
    rating: 4.5,
    participation: 8,
    intro: "데이터 기반으로 문제를 해결하는 기획자입니다."
  },
  {
    id: 103,
    user: { username: "김서버" },
    skills: ["Java", "Spring", "JPA", "MySQL"],
    keywords: ["문제해결", "논리력", "끈기"],
    mainRole: "백엔드 개발자",
    subRole: "DBA",
    rating: 4.7,
    participation: 3,
    intro: "안정적이고 확장성 있는 서버를 구축합니다."
  },
  {
    id: 104,
    user: { username: "이디자인" },
    skills: ["Figma", "Adobe XD", "Zeplin"],
    keywords: ["창의력", "공감력", "협업"],
    mainRole: "UI/UX 디자이너",
    subRole: "그래픽 디자이너",
    rating: 4.9,
    participation: 12,
    intro: "직관적이고 아름다운 디자인을 추구합니다."
  },
];


function TeamMatching2() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [openMenus, setOpenMenus] = useState({});
  const [userType, setUserType] = useState(null);
  const [memberRegistered, setMemberRegistered] = useState(false);
  const [myProfile, setMyProfile] = useState({
    user: { username: "이명준" },
    skills: [],
    mainRole: "",
    subRole: "",
    keywords: [],
    intro: "",
  });
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [filterMode, setFilterMode] = useState(null);
  const [filter, setFilter] = useState({ role: "", skill: "", minRating: 0 });
  const [newTeamInfo, setNewTeamInfo] = useState({
    skills: "",
    lookingFor: "",
    category: "",
    maxMembers: 6,
    intro: "",
  });
  const [modalMember, setModalMember] = useState(null);
  const [sentInvites, setSentInvites] = useState([]);
  const [sentApplications, setSentApplications] = useState([]);
  const [inviteMap, setInviteMap] = useState({}); // { userId: [ { id, leader } ] }
  const [applicationMap, setApplicationMap] = useState({}); // { teamId: [ userObj, ... ] }
  const receivedInvites = inviteMap[myProfile.id] || [];
  const receivedApplications = applicationMap[selectedTeam?.id] || [];
  const navigate = useNavigate();
  const [teamList, setTeamList] = useState([]);
  const [applicants, setApplicants] = useState(baseApplicants);
  const [lastCreatedTeam, setLastCreatedTeam] = useState(null); // 마지막으로 생성한 팀 정보를 기억
  const [wasRegisteredAsMember, setWasRegisteredAsMember] = useState(false); // 팀원으로 등록한 사실을 기억


  const filteredApplicants = applicants.filter(
  (u) => {
    const roleMatch = filter.role ? u.mainRole?.includes(filter.role) : true;
    const skillMatch = filter.skill
      ? (u.skills || []).some((s) => s.includes(filter.skill))
      : true;
    const ratingMatch = u.rating >= filter.minRating;
    return roleMatch && skillMatch && ratingMatch;
  }
);

  useEffect(() => {
  const fetchTeams = async () => {
    try {
      const teamData = await getTeamList();
      setTeamList(teamData); 
    } catch (err) {
      toast.error("팀 목록 불러오기 실패");
      console.error(err);
    }
  };
  fetchTeams();
}, []);
useEffect(() => {
  const fetchInitialData = async () => {
    try {
      const realApplicants = await getApplicants(); // 1. 실제 데이터 불러오기

      // 2. 더미 데이터와 실제 데이터를 합치기 (중복 제거)
      const combinedData = new Map();
      baseApplicants.forEach(app => combinedData.set(app.id, app)); // 더미 먼저 추가
      (realApplicants || []).forEach(app => combinedData.set(app.id, app)); // 실제 데이터로 덮어쓰기

      // 3. 합쳐진 데이터를 상태로 설정
      setApplicants(Array.from(combinedData.values()));

    } catch (err) {
      // API 로딩 실패 시, 더미 데이터만 표시
      setApplicants(baseApplicants);
      toast.error("지원자 목록 로딩에 실패하여 임시 데이터를 표시합니다.");
      console.error(err);
    }
  };
  if (userType) {
    fetchInitialData();
  }
}, [userType]);

  const sourceTeams = teamList.length ? teamList : baseTeams;

  const dummyTeams = sourceTeams.map((team) => {
    const leaderAsMember = {
      name: team.leader,
      skills: team.skills || [],
      mainRole: team.mainRole || "팀장",
      subRole: team.subRole || "-",
      keywords: team.keywords || ["리더십"],
      rating: team.rating ?? 0,
      participation: team.participation ?? 0,
      intro: team.intro || "",
    };

    return {
      ...team,
      members: [leaderAsMember],
    };
  });

  

  const forceAccept = async (applicant) => {
    // API 연동
    try {
      await acceptApplicant(selectedTeam.id, applicant.id);
      toast.success("지원자를 팀에 추가했어요!");
    } catch (err) {
      toast.error("추가 실패");
      console.error(err);
    }
  };

  const MemberModal = ({ member, onClose }) => {
    if (!member) return null;
    return (
      <div className="modal-backdrop">
        <div className="modal-box">
          <h3>{member.name} 님의 정보</h3>
          <p>
            <strong>기술:</strong> {member?.skills?.join(", ") || "-"}
          </p>
          <p>
            <strong>역할:</strong> {member.mainRole || "-"}
          </p>
          <p>
            <strong>역량:</strong> {member.keywords?.join(", ") || "-"}
          </p>
          <button
            onClick={onClose}
            className="cta-button"
            style={{ marginTop: "1rem" }}
          >
            닫기
          </button>
        </div>
      </div>
    );
  };

  const toggleKeyword = (kw) => {
    setMyProfile((p) => {
      const has = p.keywords.includes(kw);
      const next = has
        ? p.keywords.filter((x) => x !== kw)
        : p.keywords.length < 3
        ? [...p.keywords, kw]
        : p.keywords;
      return { ...p, keywords: next };
    });
  };

  const handleCreateTeam = async () => {
  const { skills, lookingFor, category, maxMembers, intro } = newTeamInfo;
  const { name, mainRole, subRole, keywords } = myProfile;

  if (
    !skills.trim() ||
    !lookingFor.trim() ||
    !category.trim() ||
    !intro.trim() ||
    !mainRole.trim() ||
    !subRole.trim() ||
    (keywords || []).length === 0 ||
    !maxMembers ||
    maxMembers < 1
  ) {
    toast.warning("모든 입력 칸을 채워주세요.");
    return;
  }
 
  const teamData = {
    leader: name,
    skills: skills.split(",").map((s) => s.trim()),
    lookingFor: lookingFor.split(",").map((s) => s.trim()),
    category,
    maxMembers,
    intro,
    leaderInfo: {
      name,
      mainRole,
      subRole,
      keywords,
    },
  };

  try {
    // API 응답을 저장하는 변수 이름을 'newTeam'으로 통일합니다.
    const newTeam = await createTeam(teamData);
    
    // 이제 모든 곳에서 'newTeam'을 올바르게 참조할 수 있습니다.
    setSelectedTeam(newTeam); 
    setLastCreatedTeam(newTeam); 
    
    toast.success("팀이 성공적으로 생성되었습니다!");

  } catch (err) {
    console.error(err);
    toast.error("팀 생성에 실패했습니다.");
  }
};

const handleDeleteTeam = async () => {
  if (!selectedTeam) return;

  if (window.confirm("정말로 팀을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")) {
    try {
      await deleteTeam(selectedTeam.id);
      toast.success("팀이 성공적으로 삭제되었습니다.");
      setLastCreatedTeam(null);

      // ★★★ 이 부분을 handleBack() 호출로 변경합니다! ★★★
      handleBack(); 

    } catch (err) {
      toast.error("팀 삭제 중 오류가 발생했습니다.");
      console.error("팀 삭제 오류:", err);
    }
  }
};

  const handleApply = (team) => {
    setApplicationMap((prev) => {
      const updated = { ...prev };
      if (!updated[team.id]) updated[team.id] = [];
      if (!updated[team.id].some((u) => u.id === myProfile.id)) {
        updated[team.id].push(myProfile);
      }
      return updated;
    });
  };

  //팀원 등록
  const handleApplyMember = async () => {
  const { skills, mainRole, subRole, intro, keywords } = myProfile;

  if (
    skills.length === 0 ||
    !mainRole.trim() ||
    !subRole.trim() ||
    !intro.trim() ||
    keywords.length === 0
  ) {
    toast.warning("모든 항목을 입력해주세요!");
    return;
  }


  try {
    // ★★★ 핵심 수정 부분! ★★★
    // 'applyToTeam' 대신 'updateUserProfile' API를 호출합니다.
    // 현재 myProfile 상태에 저장된 사용자 정보를 서버로 보냅니다.
    await updateUserProfile(myProfile);

    toast.success("프로필이 성공적으로 등록되었습니다!");
    setMemberRegistered(true); // 등록 완료 후, 팀 목록을 보는 화면으로 전환
    setWasRegisteredAsMember(true); 
  } catch (err) {
    console.error("프로필 등록 오류:", err);
    // 토스트 메시지를 좀 더 명확하게 변경
    toast.error("프로필 등록 중 오류가 발생했습니다.");
  }
};

  const handleInvite = async (targetUser) => {
    try {
      await sendInvite(selectedTeam.id, targetUser.id, myProfile.id);
      toast.success("초대가 완료되었습니다!");

      setSentInvites(prev => [...prev, targetUser]);
    } catch (err) {
      toast.error("초대 실패");
      console.error(err);
    }
  };

  const handleBack = () => {
    setUserType(null);
    setMemberRegistered(false);
    setSelectedTeam(null);
  };

const handleApplyToTeam = async (team) => {
  try {
    // 기존 API 호출
    await applyToTeam(team.id, myProfile.id); 
    toast.success("신청이 완료되었습니다!");

    // --- 여기부터 추가 ---
    // 신청 성공 시, sentApplications 상태에 해당 팀 추가
    setSentApplications((prev) => {
      // 중복 추가 방지
      if (prev.some(t => t.id === team.id)) {
        return prev;
      }
      return [...prev, team];
    });


  } catch (err) {
    toast.error("신청 중 오류가 발생했습니다.");
    console.error(err);
  }
};

  const handleAcceptInvite = async (user, team) => {
    try {
      await respondToInvite(team.id, user.id, true);
      toast.success("초대를 수락했어요!");
    } catch (err) {
      toast.error("수락 실패");
      console.error(err);
    }
  };

  const handleRejectInvite = async (teamId) => {
    try {
      await respondToInvite(teamId, myProfile.id, false);
      toast.success("초대를 거절했어요.");
    } catch (err) {
      toast.error("거절 실패");
      console.error(err);
    }
  };

  const handleRejectApplication = (name) => {
    setApplicationMap((prev) => {
      const updated = { ...prev };
      if (updated[selectedTeam?.id]) {
        updated[selectedTeam.id] = updated[selectedTeam.id].filter(
          (u) => u.name !== name
        );
      }
      return updated;
    });
  };

  useEffect(() => {
    const fetchApplicants = async () => {
      try {
        const data = await getApplicants();
        setApplicants(data);
      } catch (err) {
        console.error("지원자 불러오기 실패", err);
      }
    };
    fetchApplicants();
  }, []);

const handleResumeAsLeader = () => {
    setUserType('leader');
    setSelectedTeam(lastCreatedTeam);
  };

  const handleResumeAsMember = () => {
    setUserType('member');
    setMemberRegistered(true);
  };

const renderTeamSlots = (team) => {
    // 디버깅을 위해 console.log를 추가하여 데이터 구조를 직접 확인해보세요.
    console.log("Rendering team members:", team.members);

    return team.members.map((member, idx) => (
      <div key={idx} className="team-member-card" style={{ width: "95%" }}>
        <p>
          👤 <strong>{member?.user?.username}</strong>
        </p>
        <p>기술 스택 : {(member.skills || []).join(", ")}</p>
        <p>희망 역할군 : {member.mainRole || "-"}</p>
        <p>보조 가능 역할군 : {member.subRole || "-"}</p>
        <p>보유 역량 : {(member.keywords || []).join(", ")}</p>
        <p>
          ⭐ {member.rating?.toFixed(1) || "4.8"} 참여{" "}
          {member.participation || 2}회
        </p>
      </div>
    ));
};

//팀원 대기열 해제
  const handleDeregisterMember = async () => {
    // 사용자에게 정말 삭제할 것인지 재확인
    if (window.confirm("팀원 대기열에서 등록을 해제하시겠습니까? 프로필 정보가 삭제됩니다.")) {
      try {
        await deregisterProfile();
        toast.success("등록이 해제되었습니다.");
        
        setWasRegisteredAsMember(false);
        // 모든 상태를 초기화하고 메인 화면으로 돌아가는 함수 호출
        handleBack(); 
        
      } catch (err) {
        toast.error("등록 해제 중 오류가 발생했습니다.");
        console.error("등록 해제 오류:", err);
      }
    }
  };

  const handleAcceptApplication = async (user) => {
    try {
      await acceptApplicant(selectedTeam.id, user.id);
      toast.success(`${user.name} 님의 신청을 수락했습니다.`);

      // 신청 목록에서 제거하고, 팀 멤버 목록에 추가
      receivedApplications((prev) => prev.filter((u) => u.id !== user.id));
      setSelectedTeam({
        ...selectedTeam,
        members: [...selectedTeam.members, user],
      });

      setUserType("member"); // 필요한 경우 유지
    } catch (err) {
      console.error("수락 중 오류 발생:", err);
      toast.error("신청 수락에 실패했습니다.");
    }
  };

  const PopularStats = ({ applicants = [] }) => {
    // 1. 역할군 카운트
    const roleCounts = {};
    applicants.forEach((u) => {
      const role = u.mainRole?.trim();
      if (role) roleCounts[role] = (roleCounts[role] || 0) + 1;
    });

    // 2. 비율 및 정렬 계산
    const entries = Object.entries(roleCounts).sort((a, b) => b[1] - a[1]);
    const total = entries.reduce((sum, [, count]) => sum + count, 0);
    const threshold = 0.05;
    const major = entries.filter(([, count]) =>
      total ? count / total >= threshold : false
    );
    const etc = entries.filter(([, count]) =>
      total ? count / total < threshold : false
    );
    const etcCount = etc.reduce((sum, [, count]) => sum + count, 0);

    // 3. 추천 공모전
    const recommendList = [
      "소프트웨어 마에스트로",
      "산학협력 프로젝트 챌린지",
      "네이버 해커톤",
      "삼성 주니어 SW 창작대회",
    ];

    // ✅ 여기서 바로 JSX 리턴
    return (
      <div className="right-widget-section">
        {/* 인기 역할군 단순 목록 */}
        <div className="widget-box">
          <h3>💡 인기 있는 역할군</h3>
          <ul>
            {entries.map(([role, count]) => (
              <li key={role}>
                <strong>{role}</strong>: {count}명
              </li>
            ))}
            {entries.length === 0 && <li>데이터 없음</li>}
          </ul>
        </div>

        {/* 비율 막대 */}
        <div className="widget-box">
          <h4>📊 대기자 역할군별 비율</h4>
          {major.map(([role, count]) => {
            const percent = total ? ((count / total) * 100).toFixed(0) : 0;
            return (
              <div key={role} className="role-bar-wrapper">
                <div>{role}</div>
                <div className="role-bar-container">
                  <div
                    className="role-bar"
                    style={{ width: `${percent}%` }}
                  ></div>
                </div>
                <div className="role-percentage">{percent}%</div>
              </div>
            );
          })}
          {etcCount > 0 && total > 0 && (
            <div className="role-bar-wrapper">
              <div>기타</div>
              <div className="role-bar-container">
                <div
                  className="role-bar"
                  style={{ width: `${((etcCount / total) * 100).toFixed(0)}%` }}
                ></div>
              </div>
              <div className="role-percentage">
                {((etcCount / total) * 100).toFixed(0)}%
              </div>
            </div>
          )}
        </div>

        {/* 추천 공모전 */}
        <div className="widget-box recommend-box">
          <h4>📌 추천 공모전</h4>
          <ul>
            {recommendList.map((r, i) => (
              <li key={i}>✅ {r}</li>
            ))}
          </ul>
        </div>
      </div>
    );
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

      <div className="matching-intro">
        <h1>
          <span className="highlight">OpenTeamUp</span> - 자유롭게 팀 결성하기
        </h1>
        <p>
          원하는 팀장을 선택하거나, 나만의 팀을 만들어 자유롭게 팀원을
          구성해보세요
        </p>
        {!userType ? (
          <div className="role-toggle">
            {lastCreatedTeam ? (
              // 생성했던 팀이 있으면 '돌아가기' 버튼 표시
            <button onClick={handleResumeAsLeader}>👩‍💼 내 팀으로 돌아가기</button>
          ) : wasRegisteredAsMember ? (
            // 등록했던 프로필이 있으면 '계속 찾기' 버튼 표시
            <button onClick={handleResumeAsMember}>👨‍👩‍👧‍👦 팀 계속 찾기</button>
          ) : (
            // 아무것도 없으면 원래 시작 버튼 표시
            <>
              <button onClick={() => setUserType("leader")}>👩‍💼 팀장 시작</button>
              <button onClick={() => setUserType("member")}>👨‍👩‍👧‍👦 팀원 시작</button>
            </>
          )}
        </div>
      ) : (
          <button className="back-button" onClick={handleBack}>
          🔙 뒤로가기
        </button>
      )}
      </div>
      {!userType && (
        <div className="matching-desc">
          <img src={tupImg} alt="팀 매칭 설명" className="matching-image" />
          <p>팀장 또는 팀원이 되어 OpenTeamUP을 시작해보세요</p>
        </div>
      )}

      <div className="main-content">
        <div className="left-pane">
          {userType === "leader" && !selectedTeam && (
            <div className="team-create-form">
              <h3>팀 생성하기</h3>
              <input
                type="text"
                placeholder="모집 역할군"
                value={newTeamInfo.lookingFor}
                onChange={(e) =>
                  setNewTeamInfo({ ...newTeamInfo, lookingFor: e.target.value })
                }
              />
              <input
                type="text"
                placeholder="공모전 분야"
                value={newTeamInfo.category}
                onChange={(e) =>
                  setNewTeamInfo({ ...newTeamInfo, category: e.target.value })
                }
              />
              <input
                type="number"
                placeholder="모집 인원"
                value={newTeamInfo.maxMembers}
                onChange={(e) =>
                  setNewTeamInfo({
                    ...newTeamInfo,
                    maxMembers: +e.target.value,
                  })
                }
              />
              <input
                type="text"
                placeholder="한 줄 소개"
                value={newTeamInfo.intro}
                onChange={(e) =>
                  setNewTeamInfo({ ...newTeamInfo, intro: e.target.value })
                }
              />
              <input
                type="text"
                placeholder="기술 스택"
                value={newTeamInfo.skills}
                onChange={(e) =>
                  setNewTeamInfo({ ...newTeamInfo, skills: e.target.value })
                }
              />
              <input
                type="text"
                placeholder="희망 역할군"
                value={myProfile.mainRole}
                onChange={(e) =>
                  setMyProfile({ ...myProfile, mainRole: e.target.value })
                }
              />
              <input
                type="text"
                placeholder="보조 가능 역할군"
                value={myProfile.subRole}
                onChange={(e) =>
                  setMyProfile({ ...myProfile, subRole: e.target.value })
                }
              />
              <div className="keyword-section">
                <p className="keyword-label">
                  나의 역량 키워드 (최대 3개 선택)
                </p>
                <div className="keyword-list">
                  {allSkills.map((kw) => (
                    <button
                      key={kw}
                      type="button"
                      className={`keyword-btn ${
                        myProfile.keywords.includes(kw) ? "selected" : ""
                      }`}
                      onClick={() => toggleKeyword(kw)}
                    >
                      {kw}
                    </button>
                  ))}
                </div>
              </div>
              <button className="cta-button" onClick={handleCreateTeam}>
                Save!
              </button>
            </div>
          )}

          {userType === "member" && !memberRegistered && (
            <div className="team-create-form">
              <h3>팀원 등록하기</h3>
              <input
                type="text"
                placeholder="기술 스택"
                value={myProfile.skills.join(",")}
                onChange={(e) =>
                  setMyProfile({
                    ...myProfile,
                    skills: e.target.value.split(","),
                  })
                }
              />
              <input
                type="text"
                placeholder="희망 역할군"
                value={myProfile.mainRole}
                onChange={(e) =>
                  setMyProfile({ ...myProfile, mainRole: e.target.value })
                }
              />
              <input
                type="text"
                placeholder="보조 가능 역할군"
                value={myProfile.subRole}
                onChange={(e) =>
                  setMyProfile({ ...myProfile, subRole: e.target.value })
                }
              />
              <input
                type="text"
                placeholder="한 줄 소개"
                value={myProfile.intro}
                onChange={(e) =>
                  setMyProfile({ ...myProfile, intro: e.target.value })
                }
              />
              <div className="keyword-section">
                <p className="keyword-label">보유 역량 (최대 3개)</p>
                <div className="keyword-list">
                  {allSkills.map((kw) => {
                    const selectedKeywords = myProfile.keywords || [];
                    const isSelected = selectedKeywords.includes(kw);

                    return (
                      <button
                        key={kw}
                        type="button"
                        className={`keyword-btn ${
                          isSelected ? "selected" : ""
                        }`}
                        onClick={() => {
                          if (isSelected) {
                            // 키워드 제거
                            setMyProfile((prev) => ({
                              ...prev,
                              keywords: selectedKeywords.filter(
                                (k) => k !== kw
                              ),
                            }));
                          } else {
                            if (selectedKeywords.length >= 3) {
                              // ✅ 알림 확실히 호출
                              setTimeout(() => {
                                alert(
                                  "역량 키워드는 최대 3개까지 선택할 수 있어요!"
                                );
                              }, 10);
                              return;
                            }

                            // 키워드 추가
                            setMyProfile((prev) => ({
                              ...prev,
                              keywords: [...selectedKeywords, kw],
                            }));
                          }
                        }}
                      >
                        {kw}
                      </button>
                    );
                  })}
                </div>
              </div>
              <button className="cta-button" onClick={handleApplyMember}>
                Save!
              </button>
            </div>
          )}

          {userType === "member" && memberRegistered && !selectedTeam && (
            <>
              <div className="log-section"></div>
              <div className="list-scroll">
  {sourceTeams.map((team) => {
    const currentMembers = (team.members || []).length;
    const maxMembers = team.max_members;
    const isFull = currentMembers >= maxMembers;
    const statusText = isFull ? "모집완료" : "모집중";

    return (
      <div key={team.id} className="room-card">
        <h4>{team?.leader?.name}님의 팀</h4>
        <p>모집 역할군 : {(team.looking_for || []).join(", ")}</p>
        <p>공모전 분야 : {team.category || "미지정"}</p>
        <p>한 줄 소개 : {team.intro}</p>
        <p>
          모집 인원 :{" "}
          <strong>
            {currentMembers} / {maxMembers}
          </strong>
        </p>
        <div className="status-and-button">
          <span className={`status-badge ${isFull ? "closed" : "open"}`}>
            {statusText}
          </span>
        </div>
        <br />
        <button
          className="cta-button"
          onClick={() => handleApplyToTeam(team)}
        >
          신청하기
        </button>
      </div>
    );
  })}
</div>
            </>
          )}

          {(userType === "leader" && selectedTeam) ||
          (userType === "member" && selectedTeam) ? (
            <div className="my-team-info">
              <h3>{userType === "leader" ? "내 팀 정보" : "신청한 팀 정보"}</h3>
              <div className="team-detail-box">
                <p><strong>모집 역할군 : </strong> {(selectedTeam.looking_for || []).join(", ")}</p>
                <p>
                  <strong>공모전 분야 : </strong>{" "}
                  {selectedTeam.category || "미지정"}
                </p>
                <p>
                  <p><strong>모집 인원 : </strong> {(selectedTeam.members || []).length} / {selectedTeam.max_members}</p>
                  {selectedTeam.maxMembers}
                </p>
                <p>
                  <strong>한 줄 소개 : </strong> {selectedTeam.intro}
                </p>
              </div>
              <h4>팀원 현황</h4>
              <div className="team-member-list">
                {renderTeamSlots(selectedTeam)}
              </div>
              {userType === 'leader' && (
                <button 
                  onClick={handleDeleteTeam} 
                  className="cta-button danger" 
                  style={{marginTop: '20px', backgroundColor: '#e74c3c'}}
                >
                  팀 삭제하기
                </button>
    )}
              {userType === "leader" && (
                <div className="log-box">
                  <h4>📤 초대한 사람 목록</h4>
                  {sentInvites.length === 0 ? (
                    <p>초대한 사람이 없습니다.</p>
                  ) : (
                    sentInvites.map((u) => (
                      <div key={u.id} className="log-entry">
                        {u.name} 님에게 초대함
                      </div>
                    ))
                  )}
                </div>
              )}
              {userType === "leader" && (
                <div className="log-box">
                  <h4>📥 신청자 목록</h4>
                  {receivedApplications.length === 0 ? (
                    <p>신청자가 없습니다.</p>
                  ) : (
                    receivedApplications.map((u) => (
                      <div key={u.name} className="log-entry">
                        {u.name} 님의 신청
                        <div className="button-group">
                          <div className="button-group">
                            <button onClick={() => forceAccept(u)}>수락</button>
                            <button
                              onClick={() => handleRejectApplication(u.name)}
                            >
                              거절
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          ) : null}
        </div>

        <div className="right-pane">
          {/* 초기 상태: 팀 미선택 상태에서 PopularStats 표시 */}
          {(userType === "leader" && !selectedTeam) ||
          (userType === "member" && !memberRegistered && !selectedTeam) ? (
            <PopularStats applicants={applicants} />
          ) : null}

          {/* 팀장 시점 + 팀 선택된 경우 → 필터/초대 UI 표시 */}
          {userType === "leader" && selectedTeam && (
            <>
              <div className="filter-bar">
                <div className="filter-row">
                  <select
                    className="custom-select"
                    value={filterMode}
                    onChange={(e) => setFilterMode(e.target.value)}
                  >
                    <option value="skills">기술 필터</option>
                    <option value="role">역할 필터</option>
                  </select>

                  {/* 항상 검색창 보이되 filterMode에 따라 placeholder 및 값/핸들러 변경 */}
                  <input
                    type="text"
                    placeholder={
                      filterMode === "skills" ? "기술 입력" : "역할 입력"
                    }
                    value={
                      filterMode === "skills" ? filter.skills : filter.role
                    }
                    onChange={(e) =>
                      setFilter({
                        ...filter,
                        [filterMode]: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="slider-container">
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="0.1"
                    value={filter.minRating}
                    onChange={(e) =>
                      setFilter({ ...filter, minRating: e.target.value })
                    }
                  />
                  <span>⭐ {filter.minRating}</span>
                </div>
              </div>

              <h4>팀을 찾고 있는 사람</h4>
              <div className="list-scroll">
              {filteredApplicants.length > 0 ? (
              filteredApplicants.map((u) => (
                <div key={u.id} className="applicant-card">
                  <div>
                    <strong>{u?.name}</strong>
                  </div>
                <div className="info-row">
                  <strong>기술 스택 : </strong> {(u.skills || []).join(", ")}
                </div>
                <div className="info-row">
                  <strong>희망 역할군 : {u.mainRole}</strong>
                </div>
              <div className="info-row">
                  <strong>보조 가능 역할군 : {u.subRole}</strong>
              </div>
              <div className="info-row">
                <strong>보유 역량 : </strong> {(u.keywords || []).join(", ")}
              </div>
              <div className="info-row">
                <strong>한 줄 소개 : {u.intro}</strong>
              </div>
              <div className="info-row">
                <p>
                  ⭐ {u.rating?.toFixed(1) || "-"} 참여{" "}
                  {u.participation || 0}회
                </p>
              </div>
              <button
                className="invite-btn"
                onClick={() => handleInvite(u)}
              >
                초대하기
              </button>
            </div>
          ))
        ) : (
          <p style={{ textAlign: 'center', color: '#888', marginTop: '20px' }}>
            현재 팀을 찾고 있는 사람이 없습니다.
          </p>
        )}
      </div>
            </>
          )}

          {/* 팀원 시점이고 팀에 이미 참여한 경우 → 공백 */}
          {userType === "member" && memberRegistered && selectedTeam && <></>}

          {/* 팀원 시점이고 팀에 아직 참여하지 않음 → 내 정보 및 신청/초대 로그 */}
          {userType === "member" && memberRegistered && (
            <div className="my-info">
              <h4>내 정보</h4>
              <p>
                <strong>이름 : {myProfile?.user?.username}</strong>
              </p>
              <p>
                <strong>기술 스택 : {(myProfile.skills || []).join(", ")}</strong>
              </p>
              <p>
                <strong>희망 역할군 : {myProfile.mainRole}</strong>
              </p>
              <p>
                <strong>보조 가능 역할군 : {myProfile.subRole}</strong>
              </p>
              <p>
                <strong>보유 역량 : {myProfile.keywords.join(", ")}</strong>{" "}
              </p>
              <p>
                <strong>한 줄 소개 : {myProfile.intro}</strong>
              </p>

              <div className="log-box">
                <h4>📤 신청한 팀</h4>
                {sentApplications.length === 0 ? (
                  <p>신청한 팀이 없습니다.</p>
                ) : (
                  sentApplications.map((t) => (
                    <div key={t.id} className="log-entry">
                      {t.leader}님의 팀에 신청함
                    </div>
                  ))
                )}
              </div>

              <div className="log-box">
                <h4>📥 받은 초대</h4>
                {receivedInvites.map((t) => (
                  <div key={t.id} className="log-entry">
                    {t.leader}님의 초대
                    <div className="button-group">
                      <button
                        onClick={() => handleAcceptInvite(t.user, t.team)}
                      >
                        수락
                      </button>
                      <button onClick={() => handleRejectInvite(t.id)}>
                        거절
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <button
                onClick={handleDeregisterMember}
                className="cta-button danger"
                style={{marginTop: '20px', backgroundColor: '#e74c3c'}}
              >
              팀원 등록 해제
              </button>

              <div className="log-box">{/* 신청한 팀 로그 */}</div>
              <div className="log-box">{/* 받은 초대 로그 */}</div>
            </div>
          )}
          
        </div>
      </div>
    </div>
  );
}
export default TeamMatching2;
