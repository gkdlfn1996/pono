## Backend
백엔드 폴더로 이동 후 아래 명령어 입력  

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

라이브러리 설치(가상 환경이 활성화된 상태에서 실행)

```bash
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