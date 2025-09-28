# ---- base: 공통 ----
FROM python:3.12-slim AS base
ENV POETRY_VIRTUALENVS_CREATE=false PIP_DISABLE_PIP_VERSION_CHECK=on
WORKDIR /app
# 빌드시 node 설치 (개발/프런트 빌드용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates git build-essential nodejs npm supervisor \
  && rm -rf /var/lib/apt/lists/*

# ---- dev: 개발용 (Django runserver + React CRA dev-server 동시 실행) ----
FROM base AS dev
WORKDIR /app
# Python 의존성
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt
# Node 의존성
COPY frontend/package*.json /app/frontend/
RUN cd /app/frontend && npm install
# 소스는 볼륨 마운트로 가져올 예정(복사 생략)
# supervisord 설정은 별도 파일로 복사
COPY supervisord.conf /app/supervisord.conf
# SQLite 파일 경로가 없으면 만들어두기
RUN mkdir -p /app/DB
EXPOSE 8000 3000
CMD ["supervisord", "-c", "/app/supervisord.conf"]

# ---- prod: 배포용(옵션) - React 빌드 + Django(gunicorn) ----
FROM base AS prod
WORKDIR /app
# 백엔드 설치
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt gunicorn
# 프런트 빌드
COPY frontend /app/frontend
RUN cd /app/frontend && npm ci && npm run build
# 백엔드 소스 복사
COPY backend /app/backend
# 정적 파일 수집(필요 시)
# ENV DJANGO_SETTINGS_MODULE=config.settings
# RUN python /app/backend/manage.py collectstatic --noinput
# 런타임
EXPOSE 8000
CMD ["bash", "-lc", "cd /app/backend && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3"]