# Python 3.11 slim 이미지 사용 (경량화)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# [수정] 경로에 backend/ 를 명시해줘야 합니다.
COPY backend/requirements.txt .

# 의존성 설치 (캐시 활용)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# [수정] 소스 코드도 backend 폴더에서 가져옵니다.
COPY backend/ .

# 포트 노출 (Railway는 $PORT 환경변수 자동 설정)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 실행 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]