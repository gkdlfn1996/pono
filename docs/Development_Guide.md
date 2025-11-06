# 개발자 참고사항
- [**Backend README**](./backend/README.md) : 백엔드/프론트엔드 수동 실행 및 디버깅
- [**Frontend README**](./frontend/README.md) : 프론트엔드 개발 및 빌드 명령어

### 1. 설정 관리 흐름
* 모든 환경 설정(포트, DB 정보 등)은 루트 디렉터리의 `config.sh` 파일에서 관리됩니다.
* pono_backend.sh와 같은 모든 실행 스크립트들은 이 파일을 source하여 환경 변수를 읽어오고, 어플리케이션은 이 환경 변수를 사용해 동작합니다.

- **환경 변수 설정 (config.sh)** :  
    
    | 변수명 (Variable) | 설명 | 기본값 (Default) |
    |--------------------|------|------------------|
    | **BACKEND_PORT** | 백엔드 FastAPI 서버가 실행될 포트 | `8000` |
    | **FRONTEND_PORT** | 프론트엔드 Vue 서버가 실행될 포트 | `8080` |
    | **SHOTGRID_SERVER_URL** | 연결할 ShotGrid 서버의 주소 | `https://idea.shotgrid.autodesk.com` |
    | **DB_HOST** | PostgreSQL 데이터베이스 서버의 호스트 | `localhost` |
    | **DB_PORT** | PostgreSQL 데이터베이스 서버의 포트 | `5432` |
    | **DB_NAME** | 사용할 데이터베이스 이름 | `shotgrid_notes_db` |
    | **DB_USER** | 데이터베이스에 접속할 사용자 이름 | `idea` |
    | **DB_PASSWORD** | 데이터베이스 사용자의 비밀번호 | `fnxmdkagh1!` |
    | **ATTACHMENT_BASE_DIR** | 첨부 파일이 저장될 기본 디렉토리 이름 | `pono_attachments` |

### 2. 첨부파일 저장 방식
* 사용자가 업로드하는 첨부파일은 config.sh의 `ATTACHMENT_BASE_DIR` 변수를 루트로 합니다.  
- 업로드된 파일들은 홈 디렉토리 아래의 `pono_attachments/{note_id}/{owner_id}/` 구조로 저장됩니다.   
- 최상위 `pono_attachments` 디렉토리는 `backend/app/main.py` 실행 시 자동으로 생성되며, 하위 디렉토리는 파일 업로드 시 동적으로 생성됩니다.

### 3. 실시간 노트 동기화
* 노트 내용은 WebSocket을 통해 클라이언트 간에 실시간으로 동기화됩니다.
* 백엔드의 app/draftnote/websocket_manager.py가 클라이언트 연결을 관리하고, 프론트엔드의 src/composables/useWebSocket.js가 메시지를 수신하여 화면을 업데이트합니다.

### 4. ShotGrid 데이터 캐싱
* ShotGrid API 호출을 최소화하기 위해, 프로젝트, 샷, 버전 등 자주 조회하는 데이터는 백엔드에서 캐시 처리됩니다.
* 캐시 관련 로직은 app/shotgrid/shotgrid_cache_manager.py에서 관리합니다. 개발 중 데이터 변경이 즉시 반영되지 않는다면 이 캐시 때문일 수 있습니다.

### 5. 데이터베이스 스키마 변경
* 데이터베이스 테이블 구조(테이블, 컬럼 등)는 `Alembic`을 통해 관리됩니다.
* 데이터베이스 모델은 `app/draftnote/database_models.py`에서 구성됩니다.
* 만약 데이터베이스의 모델을 변경했다면, 반드시 터미널에서 새로운 리비전 파일을 생성(alembic revision --autogenerate -m "변경 내용 요약")하고 데이터베이스에 적용(alembic upgrade head)해야 합니다.