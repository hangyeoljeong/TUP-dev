# ---- backend/Dockerfile ----
FROM python:3.12-slim
WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates git build-essential supervisor \
  && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# 소스 코드 복사
COPY backend /app/backend

EXPOSE 8000
CMD ["python", "backend/manage.py", "runserver", "0.0.0.0:8000"]