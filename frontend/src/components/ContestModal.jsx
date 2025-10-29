import React, { useState, useEffect, useRef } from 'react';
import Modal from '@mui/material/Modal';
import CloseIcon from '@mui/icons-material/Close';
import SkillManager from './SkillManager';
import TeamList from './TeamList';
import FeedbackModal from './FeedbackModal';
import { calculateDday } from '../utils/dateUtils';
import GroupsIcon from '@mui/icons-material/Groups';
import { toast } from 'react-toastify';
import {
  saveUserInput,
  getWaitingUsers,
  applyTeamup,
  getMatchedTeams,
  applyTeamRematch,
  performFeedbackAction,
} from '../api/teamup1';

const ContestModal = ({
  open,
  onClose,
  selectedContest,
  users,
  setUsers,
  userSkills,
  setUserSkills,
  currentUser,
}) => {
  const [mainRole, setMainRole] = useState('');
  const [subRole, setSubRole] = useState('');
  const [matched, setMatched] = useState([]);
  const [myTeam, setMyTeam] = useState(null); // ✅ 내 팀 상태로 관리
  const [feedbacks, setFeedbacks] = useState({});
  const [rawTeams, setRawTeams] = useState([]);
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);

  const hasShownToast = useRef(false);
  const formRef = useRef(null);
  const queueRef = useRef(null);

  

  useEffect(() => {
    const saved = localStorage.getItem('userInput');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setUserSkills(parsed.keywords || parsed.skills || []); 
        setMainRole(parsed.mainRole || '');
        setSubRole(parsed.subRole || '');
        console.log('💾 이전 입력 복원됨:', parsed);
      } catch (err) {
        console.error('❌ 저장된 입력 복원 실패:', err);
      }
    }
  }, []);


  const scrollToBoth = () => {
    formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    queueRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const [isHovered, setIsHovered] = useState(false);
  const [isTeamHovered, setIsTeamHovered] = useState(false);
  const [isFeedbackHovered, setIsFeedbackHovered] = useState(false);
  const [isTeamroomHovered, setIsTeamroomHovered] = useState(false);

  // ✅ 입력 안내 토스트
  useEffect(() => {
    const alreadySaved = users.some((u) => u.id === currentUser?.id);
    if (open && !hasShownToast.current && !alreadySaved) {
      toast.info('공모전 입력란(역량 키워드, 역할군 등)을 먼저 작성해주세요!');
      hasShownToast.current = true;
    }
  }, [open, users, currentUser]);

  // ✅ 모달 열릴 때 서버에서 팀 목록 불러오기
  useEffect(() => {
    if (!open || !selectedContest?.id) return;
    (async () => {
      try {
        const list = await getMatchedTeams();
        if (Array.isArray(list)) {
          setRawTeams(list);
          const hydrate = (members) =>
            members.map((m) => {
              const u = users.find((u) => u.id === m.id);
              return {
                id: m.id,
                name: m.name || u?.name || `User ${m.id}`,
                mainRole: m.mainRole || m.main_role || u?.mainRole || '',
                subRole: m.subRole || m.sub_role || u?.subRole || '',
                skills: m.skills || u?.skills || [],
                keywords: [...(m.keywords || u?.keywords || [])],
                rating: m.rating ?? u?.rating,
                participation: m.participation ?? u?.participation,
              };
            });
          setMatched(list.map((t) => hydrate(t.members)));
        }
      } catch (e) {
        console.error(e);
      }
    })();
  }, [open, selectedContest?.id]);

  // ✅ 내 팀 자동 계산 (matched 변경 시 반영)
  useEffect(() => {
    if (!matched || !currentUser) return;
    const found = matched.find((team) =>
      team.some((m) => m.id === currentUser?.id)
    );
    if (found && JSON.stringify(found) !== JSON.stringify(myTeam)) {
      setMyTeam(found);
      console.log('🌀 useEffect 기반 myTeam 갱신');
    }
  }, [JSON.stringify(matched), currentUser?.id]);

  const isMatched = !!myTeam;

  // ✅ refreshTeams (팀 & 대기열 즉시 갱신)
  const refreshTeams = async () => {
    try {
      console.log('📡 최신 팀 목록 불러오는 중...');
      const [teamsRes, waitingRes] = await Promise.all([
        getMatchedTeams(),
        getWaitingUsers(),
      ]);

      const updatedTeams = Array.isArray(teamsRes?.data) ? teamsRes.data : teamsRes;
      const waitingUsersData =
        waitingRes?.data?.waiting_users || waitingRes?.waiting_users || [];

      const hydrate = (members) =>
        members.map((m) => {
          const u = users.find((u) => u.id === m.id);
          return {
            id: m.id,
            name: m.name || u?.name || `User ${m.id}`,
            mainRole: m.mainRole || u?.mainRole || '',
            subRole: m.subRole || u?.subRole || '',
            skills: [...(m.skills || u?.skills || [])], // 새 배열 복사
            keywords: [...(m.keywords || u?.keywords || [])],
            rating: m.rating ?? u?.rating,
            participation: m.participation ?? u?.participation,
          };
        });

      const newTeams = updatedTeams.map((t) => ({
        ...t,
        members: hydrate(t.members || []),
      }));

      setRawTeams([...newTeams]);
      setMatched(newTeams.map((t) => [...t.members]));
      setUsers([...waitingUsersData]);

      // ✅ 내 팀도 즉시 업데이트
      const newMyTeam = newTeams.find((t) =>
        t.members.some((m) => m.id === currentUser?.id)
      );
      setMyTeam(newMyTeam || null);

      console.log('✅ refreshTeams 완료 - 새 팀:', newMyTeam);
    } catch (err) {
      console.error('❌ refreshTeams 실패:', err);
    }
  };

  // ✅ 피드백 클릭
  const handleFeedback = async (memberId, symbol) => {
    console.log('💬 피드백 클릭됨:', memberId, symbol);

    const rawMyTeam = rawTeams.find(
      (t) => Array.isArray(t.members) && t.members.some((m) => m.id === currentUser?.id)
    );
    const teamId = rawMyTeam?.teamId || rawMyTeam?.team_id;

    if (!teamId) {
      return;
    }

    try {
      const res = await performFeedbackAction({
        action: 'feedback',
        teamId,
        userId: memberId,
        agree: symbol === '👍',
      });

      console.log('✅ 피드백 전송 성공:', res);

      setFeedbacks((prev) => ({ ...prev, [memberId]: symbol }));
    } catch (err) {
      console.error('❌ 피드백 실패:', err);
    }
  };

  // ✅ 재매칭 함수 (자동 새로고침 버전)
  const handleRematch = async () => {
    const myTeam = matched.find((team) =>
      team.some((member) => member.id === currentUser?.id)
    );
    if (!myTeam) return;

    const agreedUsers = myTeam.filter((member) => feedbacks[member.id] === '👍');

    const rawMyTeam = rawTeams.find(
      (t) => Array.isArray(t.members) && t.members.some((m) => m.id === currentUser?.id)
    );
    const teamId = rawMyTeam?.teamId || rawMyTeam?.team_id;

    if (!teamId) {
      return;
    }

    try {
      console.log('🚀 재매칭 요청 시작');
      const res = await applyTeamRematch({
        contestId: selectedContest.id,
        agreedUserIds: agreedUsers.map((u) => u.id),
        teamId,
      });

      const message =
        res?.message ||
        res?.data?.message ||
        (typeof res === 'string' ? res : null);

      if (!message?.includes('완료')) {
        toast.warning('서버에서 재매칭 완료 응답이 오지 않았습니다.');
        return;
      }


      // ✅ 1초 뒤 페이지 새로고침
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (err) {
      console.error('❌ 재매칭 오류:', err);
      toast.error(err.message || '재매칭 중 오류 발생');
    }
  };

  // ✅ 저장 버튼
  const handleSave = async () => {
    if (isMatched) {
      toast.warning('이미 팀에 속해 있어 수정할 수 없습니다.');
      return;
    }

    if (userSkills.length === 0 || !mainRole.trim() || !subRole.trim()) {
      return;
    }

    const newUser = {
      id: currentUser.id,
      name: currentUser.name || '나',
      // ⚠️ userSkills는 사실 "키워드"이므로 아래처럼 분리
      keywords: userSkills,
      skills: [], // 아직 별도 입력 없음 (나중에 추가 가능)
      mainRole,
      subRole,
    };

    try {
      const res = await saveUserInput({
        userId: newUser.id,
        keywords: newUser.keywords,  // ✅ 추가됨
        skills: newUser.skills,      // ✅ 빈 배열이더라도 명시
        mainRole: newUser.mainRole,
        subRole: newUser.subRole,
      });

      if (res?.message) {
        localStorage.setItem(
          'userInput',
          JSON.stringify({
            keywords: userSkills, // ✅ 명시적으로 keywords로 저장
            mainRole,
            subRole,
          })
        );

        setUsers((prev) => [...prev.filter((u) => u.id !== newUser.id), newUser]);
        toast.success('저장 완료!');
        await refreshTeams();   // 최신 대기열/팀 목록 즉시 반영
      }
    } catch (e) {
      toast.error('네트워크 오류');
    }
  };
  // ✅ 팀 매칭
  const matchTeam = async () => {
    if (users.length < 4) {
      toast.info('대기 인원이 부족해요! 팀업을 기다려주세요 😊');
      return;
    }

    try {
      const res = await applyTeamup(currentUser.id);
      toast.success(res?.message || '팀 매칭 완료!');
      await refreshTeams();
    } catch (e) {
      toast.error('매칭 중 오류');
    }
  };

  if (!selectedContest) return null;

  const { title, image, category, deadline, start, organizer } = selectedContest;
  const rawMyTeam = rawTeams.find(
    (t) => Array.isArray(t.members) && t.members.some((m) => m.id === currentUser?.id)
  );
  const teamIdForModal = rawMyTeam?.teamId || null;

   return (
    <>
      <Modal open={open} onClose={onClose}>
        <div
          style={{
            width: '100vw',
            height: '100vh',
            backgroundColor: 'white',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              padding: '1rem',
            }}
          >
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '1.5rem',
                cursor: 'pointer',
              }}
            >
              <CloseIcon />
            </button>
          </div>

          <div
            style={{
              display: 'flex',
              flex: 1,
              overflow: 'hidden',
              padding: '0 2rem 2rem 2rem',
              gap: '2rem',
            }}
          >
            <div style={{ width: '40%', overflowY: 'auto' }}>
              <img
                src={image}
                alt="공모전"
                style={{
                  width: '100%',
                  borderRadius: '8px',
                  marginBottom: '1rem',
                }}
              />
              <h2
                style={{
                  fontFamily: "'Montserrat', 'Noto Sans KR'",
                  fontWeight: 800,
                }}
              >
                {title}
              </h2>
              <div
                style={{
                  background: '#F8F9FA',
                  padding: '1rem',
                  borderRadius: '8px',
                }}
              >
                <p>• 주최: {organizer}</p>
                <p>
                  • 일정: {start} ~ {deadline}
                </p>
                <p>• 마감: {calculateDday(deadline)}</p>
                <p>• 분야: {category}</p>
              </div>

              <div ref={formRef} style={{ marginTop: '1rem' }}>
                <SkillManager
                  skills={userSkills}
                  setSkills={setUserSkills}
                  mainRole={mainRole}
                  setMainRole={setMainRole}
                  subRole={subRole}
                  setSubRole={setSubRole}
                  disabled={isMatched}
                />
                {isMatched && (
                  <p
                    style={{
                      color: '#999',
                      fontSize: '0.9rem',
                      marginTop: '0.5rem',
                    }}
                  >
                    ⚠ 팀에 속한 상태에서는 입력을 수정할 수 없습니다.
                  </p>
                )}
                <button
                  onClick={handleSave}
                  disabled={isMatched}
                  onMouseEnter={() => setIsHovered(true)}
                  onMouseLeave={() => setIsHovered(false)}
                  style={{
                    width: '100%',
                    padding: '1rem',
                    backgroundColor: isMatched
                      ? '#ccc'
                      : isHovered
                        ? '#ff824e' // hover 시 밝은 오렌지
                        : '#FF6B35',
                    color: 'white',
                    border: 'none',
                    borderRadius: '10px',
                    fontSize: '1.1rem',
                    fontWeight: 700,
                    marginTop: '1.5rem',
                    fontFamily: "'Montserrat', 'Noto Sans KR'",
                    cursor: isMatched ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    boxShadow: isMatched ? 'none' : '0 2px 6px rgba(0, 0, 0, 0.15)',
                    transition: 'all 0.2s ease-in-out',
                    transform: isHovered && !isMatched ? 'translateY(-1px)' : 'translateY(0)',
                  }}
                >
                  Save!
                </button>
              </div>
            </div>

            <div style={{ width: '60%', overflowY: 'auto' }}>
              <h2
                style={{
                  color: '#FF6B35',
                  fontFamily: "'Montserrat', 'Noto Sans KR'",
                  fontWeight: 800,
                }}
              >
                <GroupsIcon style={{ marginRight: '0.5rem' }} />
                함께하자 팀으로!
              </h2>

              <div
                ref={queueRef}
                style={{
                  listStyle: 'none',
                  padding: 0,
                  maxHeight: '200px',
                  overflowY: 'auto',
                  marginBottom: '1rem',
                  background: '#FFF9F7',
                  borderRadius: '8px',
                  paddingInline: '1rem',
                }}
              >
                {users.length > 0 ? (
                  users.map((user) => (
                    <li
                    key={user.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0.8rem 0',
                      borderBottom: '1px solid #eee',
                      fontWeight: 500,
                      fontSize: '1rem',
                      color: '#333',
                    }}
                  >
                    👤 {user.name}
                  </li>
                ))
              ) : (
                <p
                  style={{
                    textAlign: 'center',
                    color: '#888',
                    padding: '1rem 0',
                    fontSize: '0.95rem',
                  }}
                >
                  🔄 대기열 데이터를 불러오는 중이거나, 현재 표시할 유저가 없습니다.
                </p>
              )}
              </div>
              {/* 팀업 버튼 또는 안내 메시지 */}
              {myTeam ? (
                <p
                  style={{
                    maxWidth: '100%',
                    width: '100%',
                    padding: '1rem',
                    background: '#FFF3ED',
                    color: '#FF6B35',
                    borderRadius: '8px',
                    textAlign: 'center',
                    fontWeight: 600,
                    fontSize: '1rem',
                    border: '1px solid #FF6B35',
                    boxSizing: 'border-box', // ✅ 패딩 포함해서 너비 계산
                  }}
                >
                  이미 팀에 속해 있어요! 결과를 기다려주세요 😊
                </p>
              ) : (
                <button
                  onClick={matchTeam}
                  onMouseEnter={() => setIsTeamHovered(true)}
                  onMouseLeave={() => setIsTeamHovered(false)}
                  style={{
                    width: '100%',
                    padding: '1rem',
                    backgroundColor: isTeamHovered ? '#ff824e' : '#FF6B35', // hover 시 밝은 주황
                    color: 'white',
                    border: 'none',
                    borderRadius: '10px',
                    cursor: 'pointer',
                    fontSize: '1.1rem',
                    fontWeight: 700,
                    marginBottom: '1rem',
                    fontFamily: "'Montserrat', 'Noto Sans KR'",
                    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.15)',
                    transition: 'all 0.2s ease-in-out',
                    transform: isTeamHovered ? 'translateY(-1px)' : 'translateY(0)',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                  }}
                >
                  <GroupsIcon style={{ marginRight: '0.5rem' }} />
                  TEAM UP!
                </button>
              )}

              {matched.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <TeamList
                    matched={matched}
                    feedbacks={feedbacks}
                    onFeedback={handleFeedback}
                    currentUser={currentUser}
                  />
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      gap: '1rem',
                      marginTop: '1.5rem',
                      paddingBottom: '1rem',
                    }}
                  >
                    <button
                      onMouseEnter={() => setIsFeedbackHovered(true)}
                      onMouseLeave={() => setIsFeedbackHovered(false)}
                      onClick={() => setIsFeedbackModalOpen(true)}
                      style={{
                        flex: 1,
                        padding: '0.9rem', // 기존 크기 유지
                        backgroundColor: isFeedbackHovered ? '#ff824e' : '#FF6B35',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '1rem',
                        fontWeight: 600,
                        fontFamily: "'Montserrat', 'Noto Sans KR'",
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        transition: 'background-color 0.2s ease, transform 0.2s ease',
                        transform: isFeedbackHovered ? 'translateY(-1px)' : 'translateY(0)',
                      }}
                    >
                      피드백 결과 확인하기
                    </button>
                    <button
                      onMouseEnter={() => setIsTeamroomHovered(true)}
                      onMouseLeave={() => setIsTeamroomHovered(false)}
                      onClick={() => window.open('/TeamPage', '_blank')}
                      style={{
                        flex: 1,
                        padding: '0.9rem', // 기존 세로 크기 유지
                        backgroundColor: isTeamroomHovered ? '#ff824e' : '#FF6B35',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '1rem',
                        fontWeight: 600,
                        fontFamily: "'Montserrat', 'Noto Sans KR'",
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        transition: 'background-color 0.2s ease, transform 0.2s ease',
                        transform: isTeamroomHovered ? 'translateY(-1px)' : 'translateY(0)',
                      }}
                    >
                      팀룸으로 이동하기
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </Modal>

      {isFeedbackModalOpen && (
        <FeedbackModal
          open={isFeedbackModalOpen}
          onClose={() => setIsFeedbackModalOpen(false)}
          team={myTeam || []}
          feedbacks={feedbacks}
          currentUser={currentUser}
          scrollToBoth={scrollToBoth}
          teamId={teamIdForModal}
          users={users}
          refreshTeams={refreshTeams} 
        />
      )}
    </>
  );
};

export default ContestModal;
