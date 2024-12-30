# Python 3.10 이미지 기반
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 의존성 복사 및 설치
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# `ccxt` 라이브러리 추가 설치
RUN pip install --no-cache-dir ccxt

# 소스 코드 복사
COPY app/ .

# Uvicorn을 사용하여 FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]