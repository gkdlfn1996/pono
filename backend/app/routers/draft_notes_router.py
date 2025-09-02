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
from ..draftnote.database import get_db, upsert_versions, upsert_note, get_notes_by_step
from ..draftnote import models

router = APIRouter(
    prefix="/api/notes",
    tags=["Notes & WebSocket"],
)

# -------------------------------------- WebSocket ---------------------------------------------
# (WebSocket 관련 코드는 변경 없음)
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}
    async def connect(self, websocket: WebSocket, version_id: int):
        await websocket.accept()
        if version_id not in self.active_connections:
            self.active_connections[version_id] = []
        self.active_connections[version_id].append(websocket)
    def disconnect(self, websocket: WebSocket, version_id: int):
        if version_id in self.active_connections:
            self.active_connections[version_id].remove(websocket)
            if not self.active_connections[version_id]:
                del self.active_connections[version_id]
    async def broadcast(self, message: str, version_id: int):
        if version_id in self.active_connections:
            for connection in self.active_connections[version_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{version_id}")
async def websocket_endpoint(websocket: WebSocket, version_id: int):
    await manager.connect(websocket, version_id)
    try:
        while True:
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
    username: str
    class Config:
        from_attributes = True

class NoteInfo(BaseModel):
    """
    클라이언트에 반환될 노트의 상세 정보를 나타내는 Pydantic 모델입니다.
    """
    id: int
    content: str
    updated_at: datetime
    owner: UserInfo
    class Config:
        from_attributes = True

# -------------------------------------- API Endpoints ---------------------------------------------

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
        # 1. 버전 정보 UPSERT (database.py의 upsert_versions 함수 호출)
        upsert_versions(db, [note_data.version_meta.dict()])
        
        # 2. 노트 정보 UPSERT (database.py의 upsert_note 함수 호출)
        # upsert_note 함수 내부에서 기존 노트가 있는지 확인하는 로직이 처리됩니다.
        note_to_save = {"version_id": note_data.version_id, "content": note_data.content}
        saved_note = upsert_note(db, note_to_save, note_data.owner_id)
        
        db.commit()
        db.refresh(saved_note)

        # 3. 웹소켓 브로드캐스트 (효율적으로 변경된 방식)
        note_info_for_broadcast = NoteInfo.from_orm(saved_note)
        await manager.broadcast(note_info_for_broadcast.json(), saved_note.version_id)

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