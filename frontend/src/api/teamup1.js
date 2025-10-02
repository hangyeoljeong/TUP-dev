import http from "../lib/http";

// 1) 사용자 입력 저장
export const saveUserInput = async (payload) => {
  const { data } = await http.post("team1/save/", payload, {
    headers: { "Content-Type": "application/json" },
  });
  return data;
};

// 2) 팀 매칭 시도
export const applyTeamup = async (userId) => {
  const { data } = await http.post(
    "team1/apply/",              // ✅ URL
    JSON.stringify({ userId }),  // ✅ body를 JSON 문자열로
    {
      headers: { "Content-Type": "application/json" }, // ✅ JSON 보낸다고 명시
    }
  );
  return data;
};

// 3) 매칭된 팀 목록 조회
export const getMatchedTeams = async () => {
  const { data } = await http.get("team1/teams/");
  return data;
};

// 4) 피드백 저장
export const submitFeedback = async ({ teamId, userId, agree }) => {
  const { data } = await http.post(
    "team1/feedback/",
    { teamId, userId, agree },
    {
      headers: { "Content-Type": "application/json" },
    }
  );
  return data;
};

// 5) 재매칭 / 대기열 이동 액션
export const performFeedbackAction = async ({ teamId, userId, action }) => {
  const { data } = await http.post("team1/submit_feedback/", {
    teamId,
    userId,
    action, // 'rematch' 또는 'requeue'
  });
  return data; // { message }
};

// 6) 대기열 사용자
export const getWaitingUsers = async () => {
  const { data } = await http.get("team1/waiting/");
  return data; // [ { userId, mainRole, subRole, skills, keywords, hasReward } ]
};

// 7) 재매칭 요청
export const applyTeamRematch = async ({ contestId, agreedUserIds, teamId }) => {
  const { data } = await http.post(
    "team1/rematch/",
    { contestId, agreedUserIds, teamId },
    {
      headers: { "Content-Type": "application/json" },
    }
  );
  return data;
};