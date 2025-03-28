# Python 3.9 기반 이미지 사용
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# 필요 파일 복사
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Flask 웹앱 복사
COPY redis_ex01.py ./

# Flask 실행 (환경 변수 설정)
ENV FLASK_APP=redis_ex01.py
ENV FLASK_RUN_HOST=0.0.0.0
EXPOSE 5000

# 컨테이너 실행 시 Flask 실행
CMD ["python", "redis_ex01.py"]
