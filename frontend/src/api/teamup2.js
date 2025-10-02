import axios from 'axios';

// 1. 팀 생성
// 경로: /api/team2/teams/create/
export const createTeam = async (teamData) => {
  const res = await axios.post('team2/teams/create/', teamData);
  return res.data;
};

// 2. 팀 리스트 조회
// 경로: /api/team2/teams/
export const getTeamList = async () => {
  const res = await axios.get('team2/teams/');
  return res.data;
};

// 3. 지원자 수락
// 경로: /api/team2/applications/:id/accept/
export const acceptApplicant = async (applicationId) => {
  const res = await axios.post(`team2/applications/${applicationId}/accept/`);
  return res.data;
};

// 4. 팀에 지원
// 경로: /api/team2/teams/:id/apply/
export const applyToTeam = async (teamId, userId) => {
  const res = await axios.post(`team2/teams/${teamId}/apply/`, {
    applicant: userId,
  });
  return res.data;
};

// 5. 초대 보내기
// 경로: /api/team2/teams/:id/invite/
export const sendInvite = async (teamId, targetUserId) => {
  const res = await axios.post(`team2/teams/${teamId}/invite/`, {
    user_id: targetUserId,
  });
  return res.data;
};

// 6. 초대 수락 / 거절
// 경로: /api/team2/invitations/:id/accept or reject
export const respondToInvite = async (inviteId, accepted) => {
  const action = accepted ? 'accept' : 'reject';
  const res = await axios.post(`team2/invitations/${inviteId}/${action}/`);
  return res.data;
};

// 7. 지원자 목록(필터링)
// 경로: /api/team2/applicants/filter/
export const getApplicants = async (filters = {}) => {
  const res = await axios.get(`team2/applicants/filter/`, { params: filters });
  return res.data;
};

// 8. 프로필 업데이트
// 경로: /api/team2/profile/update/
export const updateUserProfile = async (profileData) => {
  const res = await axios.post('team2/profile/update/', profileData);
  return res.data;
};

// 9. 팀 상세 정보 조회
// 경로: /api/team2/teams/:id/
export const getTeamDetails = async (teamId) => {
  const res = await axios.get(`team2/teams/${teamId}/`);
  return res.data;
};

// 10. 팀 삭제
// 경로: /api/team2/teams/:id/
export const deleteTeam = async (teamId) => {
  const res = await axios.delete(`team2/teams/${teamId}/`);
  return res.data;
};

// 11. 팀원 대기열 해제
// 경로: /api/team2/profile/update/
export const deregisterProfile = async () => {
  const res = await axios.delete(`team2/profile/update/`);
  return res.data;
};