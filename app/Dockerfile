# Python 3.10 이미지 기반
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 복사 및 설치
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY app/ .

# Uvicorn을 사용하여 FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]