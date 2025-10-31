"""
notes_router 모듈

이 모듈은 임시 노트 및 웹소켓과 관련된 API 엔드포인트(경로)를 정의합니다.
실제 로직 처리는 `draftnote_api.py`에 위임합니다.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

# 분리된 모듈들 임포트
from ..draftnote import database
from ..draftnote import database_models as models
from ..draftnote import draftnote_schema as schemas
from ..draftnote import draftnote_api
from ..draftnote import websocket_manager

router = APIRouter(
    prefix="/api/notes",
    tags=["Notes & WebSocket"],
)

# -------------------------------------- WebSocket API Endpoints ---------------------------------------------

@router.websocket("/ws/{version_id}")
async def websocket_endpoint(websocket: WebSocket, version_id: int):
    """클라이언트의 WebSocket 연결을 처리하는 엔드포인트입니다."""
    await websocket_manager.manager.connect(websocket, version_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.manager.disconnect(websocket, version_id)

# -------------------------------------- Dratf Notes API Endpoints ---------------------------------------------

@router.post("/", response_model=schemas.NoteInfo)
async def create_or_update_note(
    note_data: schemas.NoteCreate,
    db: Session = Depends(database.get_db)
):
    """새로운 임시 노트를 생성/업데이트/삭제합니다."""
    return await draftnote_api.save_note_logic(note_data, db)

@router.get("/by_step", response_model=List[schemas.NoteInfo])
async def get_all_notes_by_step(
    project_id: int,
    step_name: str,
    db: Session = Depends(database.get_db)
):
    """특정 프로젝트와 스텝에 속한 모든 노트를 조회합니다."""
    return database.get_notes_by_step(db, project_id=project_id, step_name=step_name)

@router.get("/{version_id}/{owner_id}", response_model=schemas.NoteInfo)
async def get_note(version_id: int, owner_id: int, db: Session = Depends(database.get_db)):
    """특정 버전 ID와 소유자 ID에 해당하는 임시 노트를 조회합니다."""
    note = db.query(models.Note).filter(
        models.Note.version_id == version_id, models.Note.owner_id == owner_id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.get("/{version_id}", response_model=List[schemas.NoteInfo])
async def get_notes_for_version(version_id: int, db: Session = Depends(database.get_db)):
    """특정 버전 ID에 연결된 모든 임시 노트를 조회합니다."""
    notes = db.query(models.Note).filter(models.Note.version_id == version_id).all()
    return notes