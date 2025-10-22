---
유저 정보 및 대기열, 팀 초기화
---
backend bash 입장 후 cd backend -> python manage.py shell
---

```bash
from TeamMatching1.models import WaitingUser, Team

WaitingUser.objects.all().delete()

Team.objects.all().delete()

print("✅ 대기열 및 팀 초기화 완료!")
```
---
처음 역량 및 역할군 입력시 캐시를 저장하여 불러오는 경우이므로 테스트할 때 캐시를 불러와서 복원함 
-> 해결법 : 개발자도구 Application - Local Storage(local:3000) - UserInput Key 삭제

