# Screen 세션 접속 및 로그 확인
### Backend
```bash
cd pono
source ./config.sh
cd "$BACKEND_DIR"
screen -r pono_backend
```

### Frontend
```bash
cd pono
source ./config.sh
cd "$BACKEND_DIR"
screen -r pono_frontend
```

### 스크린 세션에서 지나간 로그 스크롤해서 보기
```bash
ctrl+A [
```
### 스크린 세션 닫기
```bash
ctrl+A D
```

<br><br>

# 변경된 Code 적용 및 서버 재시작(권장)
1. PONO서버 접속
2. pono프로젝트 경로 들어가기
3. Git에서 변경사항 pull받기
4. 아래 명령어 입력

    ```bash
    cd pono
    source ./config.sh
    cd "$BACKEND_DIR"
    ./bin/pono_launcher.sh
    ```
### Backend만 재실행
```bash
cd pono
source ./config.sh
cd "$BACKEND_DIR"
./bin/pono_backend.sh
```
### Frontend만 재실행
```bash
cd pono
source ./config.sh
cd "$BACKEND_DIR"
./bin/pono_frontend.sh
```

<br><br>

# 문제 해결 및 서버 수동 실행
`pono_backend.sh` 또는 `pono_frontend.sh` 스크립트가 정상적으로 동작하지 않거나, 세션 내부를 직접 제어해야 할 때 아래 방법을 사용합니다.

<br>

## Backend 스크린 세션 강제 종료
기존 `pono_backend` 세션이 응답하지 않을 경우, 다음 명령어로 세션을 완전히 종료할 수 있습니다.
```bash
screen -S pono_backend -X quit
```

<br><br>

## Backend 수동 실행
백엔드 스크린 세션 생성
```bash
screen -S pono_backend
```

백엔드 폴더로 이동
```bash
cd pono
source ./config.sh
cd "$BACKEND_DIR"
```

가상환경 활성화 (Screen 세션 내부에서)
```bash
source .venv/bin/activate
```

의존성 설치 (가상 환경이 활성화된 상태에서 필요시 실행)

```bash
python -m pip install --no-user -r requirements.txt
```
서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

스크린 세션에서 지나간 로그 스크롤해서 보기
```bash
ctrl+A [
```
스크린 세션 닫기
```bash
ctrl+A D
```

<br><br>

## Frontend 스크린 세션 강제 종료
기존 `pono_frontend` 세션이 응답하지 않을 경우, 다음 명령어로 세션을 완전히 종료할 수 있습니다.
```bash
screen -S pono_frontend -X quit
```
<br><br>

## Frontend 수동 실행

프론트엔드 스크린 세션 생성
```bash
screen -S pono_frontend
```

프론트엔드 폴더로 이동 
```bash
cd pono
source ./config.sh
cd "$FRONTEND_DIR"
```

프론트엔드 서버 실행
```bash
npm install && npm run serve
```

<br><br>

# Database 스키마 관리 (Alembic)
**`pono_backend.sh`** 스크립트를 실행하면 서버 시작 전에 자동으로 `alembic upgrade head` 명령이 실행되어, **`backend/alembic/versions/`** 디렉토리에 있는 최신 마이그레이션 스크립트가 데이터베이스에 적용됩니다. 

따라서 다른 사람이 DB 모델을 수정하고 Git에 푸시한 변경사항을 받아온 경우, 별도의 수동 작업 없이 **`pono_backend.sh`** 실행만으로 데이터베이스가 업데이트됩니다.

> ⚠️ **내가 직접 DB모델을 수정 했을 때는 아래 명령어를 꼭 실행해주세요.**

<br>

**1. 가상환경 활성화**  
```bash
cd pono
source ./config.sh
cd "$BACKEND_DIR"
source .venv/bin/activate
```

<br>

**2. 마이그레이션 스크립트 자동 생성**  
```bash
alembic revision --autogenerate -m "변경 내용에 대한 간략한 설명"
```

<br>

**3. 생성된 파일 확인 및 커밋**  

- **backend/alembic/versions/** 디렉토리에 새로 생성된 파이썬 파일확인 및 git 커밋하기

**4. 가상환경 종료**
```bash
deactivate
```


<br><br>

# IP
### 개발 서버
- Backend : 30.0.1.141:8000
- Frontend : 30.0.1.141:8080

### PONO 운용 서버 
- Backend : 10.0.1.110:8000
- Frontend : 10.0.1.110:8080

<br><br>

# 설정
- **첨부파일 저장 경로**:   
    업로드된 파일들은 홈 디렉토리 아래의 `pono_attachments/{note_id}/{owner_id}/` 구조로 저장됩니다. 최상위 `pono_attachments` 디렉토리는 `/backend/app/main.py` 실행 시 자동으로 생성되며, 하위 디렉토리는 파일 업로드 시 동적으로 생성됩니다.
