# ---- frontend/Dockerfile ----
FROM node:20
WORKDIR /app

# package.json, package-lock.json만 복사 (frontend 폴더 안의 것)
COPY frontend/package*.json ./

# 의존성 설치
RUN npm install

# frontend 소스 복사
COPY frontend /app

EXPOSE 3000
CMD ["npm", "start"]