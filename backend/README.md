## Backend
백엔드 폴더로 이동 후 아래 명령어 입력  

```bash
source .venv/bin/activate
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
python run.py
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

<br>

## 설정
- **첨부파일 저장 경로**: 업로드된 파일들은 홈 디렉토리 아래의 `pono_attachments/{note_id}/{owner_id}/` 구조로 저장됩니다. 최상위 `pono_attachments` 디렉토리는 `python run.py` 실행 시 자동으로 생성되며, 하위 디렉토리는 파일 업로드 시 동적으로 생성됩니다.
