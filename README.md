# pono
ShotGrid의 샷 및 버전 정보를 활용하여, 사용자들이 특정 버전에 대한 임시 노트를 실시간으로 작성하고 관리할 수 있는 웹 싱글 페이지 애플리케이션


<br>
<br>

## Backend
백엔드 폴더로 이동 후 아래 명령어 입력  

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```
필요시 라이브러리 재설치
```bash
# 라이브러리 설치(가상 환경이 활성화된 상태에서 실행)
cd app/
python -m pip install --no-user -r requirements.txt
```
<br>
<br>

## Frontend
프론트엔드 폴더로 이동 후 아래 명령어 입력

```bash
npm run serve
```

<br>
<br>

## IP
### 개발 서버
- Backend : 30.0.1.141:8001
- Frontend : 30.0.1.141:8081

### PONO
- Backend : 10.0.1.110:8001
- Frontend : 10.0.1.110:8081