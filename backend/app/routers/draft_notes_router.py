"""
notes_router 모듈

이 모듈은 임시 노트 기능과 관련된 API 엔드포인트를 정의합니다.
노트의 생성, 조회, 업데이트를 처리하며, 웹소켓을 통해 실시간으로 노트 변경 사항을
클라이언트들에게 브로드캐스트합니다.

주요 기능:
- 웹소켓 연결 관리 및 메시지 브로드캐스트
- 노트 데이터의 Pydantic 모델 정의 (API 요청/응답 유효성 검사 및 직렬화)
- 노트 생성/업데이트 (POST /api/notes)
- 특정 사용자 노트 조회 (GET /api/notes/{version_id}/{owner_id})
- 특정 버전의 모든 노트 조회 (GET /api/notes/{version_id})
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

# 사용자님 스타일대로 get_db와 crud 함수들을 직접 임포트
from ..draftnote.database import get_db, upsert_versions, upsert_note
from ..draftnote.database import get_notes_by_step, delete_note_if_exists
from ..draftnote import models

router = APIRouter(
    prefix="/api/notes",
    tags=["Notes & WebSocket"],
)

# -------------------------------------- WebSocket ---------------------------------------------

class ConnectionManager:
    """
    활성 WebSocket 연결을 관리하는 클래스입니다.
    각 버전 ID별로 연결된 클라이언트들을 그룹화하여, 특정 버전의 클라이언트들에게만
    메시지를 보낼 수 있도록 합니다.

    버전 ID별로 연결을 그룹화하여 특정 버전의 클라이언트에게 메시지를 보낼 수 있습니다.
    """

    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, version_id: int):
        """
        새로운 WebSocket 연결을 수락하고, 해당 버전 ID에 연결된 클라이언트 목록에 추가합니다.
        """
        await websocket.accept()
        if version_id not in self.active_connections:
            self.active_connections[version_id] = []
        self.active_connections[version_id].append(websocket)
        # print(f"[WebSocket] CONNECTED: version_id={version_id}, client={websocket.client}")
        # print(f"[WebSocket] Active connections for {version_id}: {len(self.active_connections[version_id])}")

    def disconnect(self, websocket: WebSocket, version_id: int):
        """
        WebSocket 연결을 해제하고, 해당 버전 ID의 클라이언트 목록에서 제거합니다.
        """
        if version_id in self.active_connections:
            self.active_connections[version_id].remove(websocket)
            # print(f"[WebSocket] DISCONNECTED: version_id={version_id}, client={websocket.client}")

            if not self.active_connections[version_id]:
                del self.active_connections[version_id]
                # print(f"[WebSocket] No more active connections for version_id={version_id}. Removing key.")


    async def broadcast(self, message: str, version_id: int):
        """
        특정 버전 ID에 연결된 모든 클라이언트에게 메시지를 브로드캐스트합니다.
        `exclude_websocket`이 지정된 경우, 해당 클라이언트에게는 메시지를 보내지 않습니다.
        (예: 메시지를 보낸 본인에게는 다시 보내지 않음)
        """
        if version_id in self.active_connections:
            for connection in self.active_connections[version_id]:
                await connection.send_text(message)
            print(f"[WebSocket] BROADCAST: message to version_id={version_id}, {len(self.active_connections[version_id])} clients.")

manager = ConnectionManager()


# -------------------------------------- WebSocket API Endpoints ---------------------------------------------

@router.websocket("/ws/{version_id}")
async def websocket_endpoint(websocket: WebSocket, version_id: int):
    """
    클라이언트의 WebSocket 연결 요청을 처리하는 엔드포인트입니다.
    연결이 수립되면 클라이언트로부터 메시지를 수신하고, 수신된 메시지를
    동일한 버전 ID에 연결된 다른 클라이언트들에게 브로드캐스트합니다.

    버전 ID별로 WebSocket 연결을 처리하는 엔드포인트입니다.
    """
    # await manager.connect(websocket, version_id)

    # print(f"[WebSocket] Endpoint: Received connection request for version_id={version_id}")
    await websocket.accept() # Try accepting directly first
    # print(f"[WebSocket] Endpoint: Connection accepted for version_id={version_id}")
    manager.active_connections.setdefault(version_id, []).append(websocket) # Manually add to manager

    try:
        # print(f"[WebSocket] Endpoint: Waiting for messages on version_id={version_id}")
        while True:
            # 클라이언트로부터 받은 메시지를 다른 클라이언트에게 브로드캐스트합니다.
            # 메시지를 보낸 클라이언트는 제외합니다
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, version_id)





# -------------------------------------- Pydantic Models ---------------------------------------------

class NoteBase(BaseModel):
    """
    노트의 기본 내용을 정의하는 Pydantic 모델입니다.
    """
    content: str

class VersionMeta(BaseModel):
    """노트 저장 시 함께 받을 버전 메타데이터 모델"""
    id: int
    name: str
    step_name: str
    project_id: int

class NoteCreate(NoteBase):
    """
    새 노트를 생성하거나 기존 노트를 업데이트할 때 사용되는 Pydantic 모델입니다.
    노트 내용 외에 ShotGrid 버전 ID와 소유자 ID를 포함합니다.
    """
    version_id: int
    owner_id: int # 사용자 ID (우리 DB의 users.id)
    version_meta: VersionMeta

class UserInfo(BaseModel):
    """
    노트 소유자의 기본 정보를 나타내는 Pydantic 모델입니다.
    """
    id: int
    username: str   # 사용자 이름
    login: str      # 사용자 로그인 ID(사번)
    class Config:
        from_attributes = True

class NoteInfo(BaseModel):
    """
    클라이언트에 반환될 노트의 상세 정보를 나타내는 Pydantic 모델입니다.
    """
    id: int
    version_id: int
    content: str
    updated_at: datetime
    owner: UserInfo
    class Config:
        from_attributes = True


# -------------------------------------- Dratf Notes API Endpoints ---------------------------------------------

@router.post("/", response_model=NoteInfo)
async def create_or_update_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db)
):
    """
    새로운 임시 노트를 생성하거나 기존 노트를 업데이트합니다 (UPSERT).
    노트가 성공적으로 저장되면, 해당 버전의 모든 연결된 클라이언트에게 웹소켓을 통해
    업데이트된 노트 정보를 브로드캐스트합니다.
    """
    try:
        # 1. 노트 내용이 비어있는지 확인 (공백만 있는 경우 포함)
        if not note_data.content.strip():
            # 내용이 비었으면: 노트 삭제
            was_deleted = delete_note_if_exists(db, note_data.version_id, note_data.owner_id)
            if was_deleted:
                db.commit()
                # 삭제 성공 시, 다른 사용자에게 빈 내용의 노트를 보내 삭제되었음을 알림
                # 프론트엔드는 content가 비어있는 NoteInfo를 받으면 목록에서 해당 노트를 제거함
                # owner.id로 노트를 식별해야 하므로, owner 정보를 포함하여 broadcast
                note_info_for_broadcast = NoteInfo(id=0, version_id=note_data.version_id, content="", updated_at=datetime.now(), owner=UserInfo(id=note_data.owner_id, username="", login=""))
                await manager.broadcast(note_info_for_broadcast.model_dump_json(), note_data.version_id)
            return {"detail": "Empty note processed."}
        else:
            # 내용이 있으면: 기존의 저장/업데이트 로직 실행
            upsert_versions(db, [note_data.version_meta.model_dump()])
            
            # 2. 노트 정보 UPSERT
            note_to_save = {"version_id": note_data.version_id, "content": note_data.content}
            saved_note = upsert_note(db, note_to_save, note_data.owner_id)
            
            db.commit()
            db.refresh(saved_note)

            # 3. 웹소켓 브로드캐스트 (Pydantic V2 호환 및 올바른 version_id 사용)
            note_info_for_broadcast = NoteInfo.model_validate(saved_note)
            await manager.broadcast(note_info_for_broadcast.model_dump_json(), saved_note.version_id)
            print(f"[WebSocket] create_or_update_note: Broadcast initiated for version_id={saved_note.version_id}.")

            return note_info_for_broadcast
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by_step", response_model=List[NoteInfo])
async def get_all_notes_by_step(
    project_id: int,
    step_name: str,
    db: Session = Depends(get_db)
):
    """
    특정 프로젝트와 스텝에 속한 모든 노트를 한 번에 조회합니다.
    """
    return get_notes_by_step(db, project_id=project_id, step_name=step_name)

@router.get("/{version_id}/{owner_id}", response_model=NoteInfo)
async def get_note(version_id: int, owner_id: int, db: Session = Depends(get_db)):
    """
    특정 버전 ID와 소유자 ID에 해당하는 임시 노트를 조회합니다.
    """
    note = db.query(models.Note).filter(
        models.Note.version_id == version_id, models.Note.owner_id == owner_id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.get("/{version_id}", response_model=List[NoteInfo])
async def get_notes_for_version(version_id: int, db: Session = Depends(get_db)):
    """
    특정 버전 ID에 연결된 모든 임시 노트를 조회합니다.
    """
    notes = db.query(models.Note).filter(models.Note.version_id == version_id).all()
    return notes