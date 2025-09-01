
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
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..draftnote.database import get_db
from ..draftnote import models # models.py 임포트

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
        await websocket.accept()
        """
        새로운 WebSocket 연결을 수락하고, 해당 버전 ID에 연결된 클라이언트 목록에 추가합니다.
        """
        if version_id not in self.active_connections:
            self.active_connections[version_id] = []
        self.active_connections[version_id].append(websocket)
        print(f"WebSocket connected: version_id={version_id}, total: {len(self.active_connections[version_id])}")

    def disconnect(self, websocket: WebSocket, version_id: int):
        if version_id in self.active_connections:
            """
            WebSocket 연결을 해제하고, 해당 버전 ID의 클라이언트 목록에서 제거합니다.
            """
            self.active_connections[version_id].remove(websocket)
            if not self.active_connections[version_id]:
                del self.active_connections[version_id]
        print(f"WebSocket disconnected: version_id={version_id}")

    async def broadcast(self, message: str, version_id: int, exclude_websocket: WebSocket = None):
        if version_id in self.active_connections:
            """
            특정 버전 ID에 연결된 모든 클라이언트에게 메시지를 브로드캐스트합니다.
            `exclude_websocket`이 지정된 경우, 해당 클라이언트에게는 메시지를 보내지 않습니다.
            (예: 메시지를 보낸 본인에게는 다시 보내지 않음)
            """
            for connection in self.active_connections[version_id]:
                if connection != exclude_websocket:
                    await connection.send_text(message)
            print(f"Broadcasted to version {version_id}: {message}")

manager = ConnectionManager()

@router.websocket("/ws/{version_id}")
async def websocket_endpoint(websocket: WebSocket, version_id: int):
    """
    클라이언트의 WebSocket 연결 요청을 처리하는 엔드포인트입니다.
    연결이 수립되면 클라이언트로부터 메시지를 수신하고, 수신된 메시지를
    동일한 버전 ID에 연결된 다른 클라이언트들에게 브로드캐스트합니다.

    버전 ID별로 WebSocket 연결을 처리하는 엔드포인트입니다.
    """
    await manager.connect(websocket, version_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 클라이언트로부터 받은 메시지를 다른 클라이언트에게 브로드캐스트합니다.
            # 메시지를 보낸 클라이언트는 제외합니다.
            await manager.broadcast(f"Client #{version_id} says: {data}", version_id, exclude_websocket=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, version_id)
        await manager.broadcast(f"Client #{version_id} left the chat", version_id)




# -------------------------------------- NoteBase ---------------------------------------------

# Pydantic 모델 정의
class NoteBase(BaseModel):
    """
    노트의 기본 내용을 정의하는 Pydantic 모델입니다.
    """
    content: str

class NoteCreate(NoteBase):
    """
    새 노트를 생성하거나 기존 노트를 업데이트할 때 사용되는 Pydantic 모델입니다.
    노트 내용 외에 ShotGrid 버전 ID와 소유자 ID를 포함합니다.
    """
    version_id: int # ShotGrid 버전 ID
    owner_id: int # 사용자 ID (우리 DB의 users.id)

class NoteUpdate(BaseModel):
    """
    노트의 내용을 업데이트할 때 사용되는 Pydantic 모델입니다.
    """
    content: str # 업데이트할 내용

# 다른 사용자 노트를 반환하기 위한 Pydantic 모델
class UserInfo(BaseModel):
    """
    노트 소유자의 기본 정보를 나타내는 Pydantic 모델입니다.
    """
    id: int
    username: str

    class Config:
        # SQLAlchemy 모델 인스턴스에서 Pydantic 모델을 생성할 수 있도록 설정합니다.
        from_attributes = True

class NoteInfo(BaseModel):
    """
    클라이언트에 반환될 노트의 상세 정보를 나타내는 Pydantic 모델입니다.
    노트 내용, 업데이트 시간, 그리고 소유자 정보를 포함합니다.
    """
    id: int
    content: str
    updated_at: datetime
    owner: UserInfo

    class Config:
        # SQLAlchemy 모델 인스턴스에서 Pydantic 모델을 생성할 수 있도록 설정합니다.
        from_attributes = True

# 노트 관련 API 엔드포인트
@router.post("/")
async def create_or_update_note(
    note_data: NoteCreate, # 노트 생성/업데이트 데이터
    db: Session = Depends(get_db)
):
    """
    새로운 임시 노트를 생성하거나 기존 노트를 업데이트합니다 (UPSERT).
    노트가 성공적으로 저장되면, 해당 버전의 모든 연결된 클라이언트에게 웹소켓을 통해
    업데이트된 노트 정보를 브로드캐스트합니다.
    """
    # 기존 노트가 있는지 확인 (version_id와 owner_id로)
    existing_note = db.query(models.Note).filter(
        models.Note.version_id == note_data.version_id,
        models.Note.owner_id == note_data.owner_id
    ).first()

    if existing_note:
        # 노트가 존재하면 업데이트
        existing_note.content = note_data.content
        existing_note.updated_at = datetime.now() # 업데이트 시간 수동 설정
        db.add(existing_note)
        db.commit()
        db.refresh(existing_note)
        
        # 웹소켓 브로드캐스트
        # NoteInfo 모델을 사용하여 브로드캐스트할 데이터 준비
        owner_user = db.query(models.User).filter(models.User.id == existing_note.owner_id).first()
        broadcast_note_info = NoteInfo(
            id=existing_note.id,
            content=existing_note.content,
            updated_at=existing_note.updated_at,
            owner=UserInfo(id=owner_user.id, username=owner_user.username)
        )
        await manager.broadcast(broadcast_note_info.json(), existing_note.version_id)

        return {"message": "Note updated successfully", "note": existing_note}
    else:
        # 노트가 없으면 새로 생성
        new_note = models.Note(**note_data.dict())
        db.add(new_note)
        db.commit()
        db.refresh(new_note)

        # 웹소켓 브로드캐스트
        owner_user = db.query(models.User).filter(models.User.id == new_note.owner_id).first()
        broadcast_note_info = NoteInfo(
            id=new_note.id,
            content=new_note.content,
            updated_at=new_note.updated_at,
            owner=UserInfo(id=owner_user.id, username=owner_user.username)
        )
        await manager.broadcast(broadcast_note_info.json(), new_note.version_id)

        return {"message": "Note created successfully", "note": new_note}

@router.get("/{version_id}/{owner_id}")
async def get_note(version_id: int, owner_id: int, db: Session = Depends(get_db)):
    """
    특정 버전 ID와 소유자 ID에 해당하는 임시 노트를 조회합니다.
    노트를 찾을 수 없으면 404 Not Found 에러를 반환합니다.
    """
    note = db.query(models.Note).filter(
        models.Note.version_id == version_id,
        models.Note.owner_id == owner_id
    ).first()
    if note:
        return {"note": note}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

@router.get("/{version_id}", response_model=List[NoteInfo])
async def get_notes_for_version(version_id: int, db: Session = Depends(get_db)):
    """
    특정 버전 ID에 연결된 모든 임시 노트를 조회합니다.
    각 노트의 내용과 함께 작성자(소유자) 정보도 포함하여 반환합니다.
    노트가 없으면 빈 리스트를 반환합니다.
    """
    notes = db.query(models.Note).filter(models.Note.version_id == version_id).all()
    if not notes:
        return [] # 노트가 없으면 빈 리스트 반환

    # NoteInfo 모델에 맞게 데이터 구조를 변환하여 반환
    # SQLAlchemy 모델 인스턴스를 Pydantic 모델로 직접 변환
    return [NoteInfo.from_orm(note) for note in notes]
