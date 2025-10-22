import React, { useEffect, useState } from "react";
import "./TeamPage.css"; // ✅ CSS 분리된 파일 import

function TeamPage() {
  const [teamData, setTeamData] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem("currentTeam");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setTeamData(parsed);
      } catch (err) {
        console.error("❌ 팀 데이터 파싱 오류:", err);
      }
    }
  }, []);

  if (!teamData || !teamData.members) {
    return (
      <div className="team-page-container">
        <h2>🚀 아직 팀 데이터가 없습니다</h2>
        <p>피드백 완료 후 팀룸으로 이동하면 여기에 팀원이 표시됩니다.</p>
      </div>
    );
  }

  const { members } = teamData;

  return (
    <div className="team-page-container">
      <header className="team-header">
        <h1>
          🤝 나의 <span style={{ color: "#FF6B35" }}>팀 프로젝트</span> 공간
        </h1>
        <p>진행 중인 팀 프로젝트 정보를 한눈에 확인하고 팀원들과 협업해보세요</p>
      </header>

      <section className="team-section">
        <h2>👥 팀원 소개</h2>
        <div className="team-grid">
          {members.map((member) => (
            <div key={member.id} className="member-card">
              <h3>{member.name}</h3>
              <p><strong>희망 역할군:</strong> {member.mainRole || "없음"}</p>
              <p><strong>보조 가능 역할군:</strong> {member.subRole || "없음"}</p>
              <p><strong>키워드:</strong> {member.keywords?.join(", ") || "없음"}</p>
              <p><strong>참여 이력:</strong> {member.participation || 0}회</p>
              <p><strong>평점:</strong> ⭐ {member.rating?.toFixed(1) || 0}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="team-section">
        <h2>📅 일정 관리</h2>
        <p>공유 캘린더 기능이 이곳에 구현될 예정입니다.</p>
      </section>

      <section className="team-section">
        <h2>📒 팀 게시판</h2>
        <p>업무, 공지사항, 회의록을 공유하는 공간입니다. (준비 중)</p>
      </section>

      <section className="team-section">
        <h2>💬 팀 채팅</h2>
        <p>실시간 커뮤니케이션 채팅 기능이 추가될 예정입니다.</p>
      </section>
    </div>
  );
}

export default TeamPage;