
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from pydantic import BaseModel

from ..shotgrid import shotgrid_api
from ..draftnote import draftnote_api, database, database_models
from ..routers.auth_router import get_shotgrid_instance

router = APIRouter(
    prefix="/api/publish",
    tags=["ShotGrid Publish"],
)

# Pydantic 모델 정의
class UserRef(BaseModel):
    type: str
    id: int

class AttachmentRef(BaseModel):
    id: int
    file_type: str
    path_or_url: str
    file_name: str | None

class PublishNotePayload(BaseModel):
    version_id: int
    project_id: int
    subject: str
    content: str
    to_users: List[UserRef]
    cc_users: List[UserRef]
    attachments: List[AttachmentRef]
    draft_note_id: int # 로컬 임시 노트를 식별하기 위한 ID
    author_id: int # API를 요청한 사용자의 ID
    task: Optional[Dict[str, Any]] = None # Task 정보 (선택적)

@router.post("/note", status_code=status.HTTP_201_CREATED)
async def publish_note_to_shotgrid(
    payload: PublishNotePayload,
    db: Session = Depends(database.get_db),
    sg = Depends(get_shotgrid_instance),
):
    """
    프론트엔드로부터 받은 데이터를 사용하여 ShotGrid에 노트를 생성하고,
    성공 시 로컬 임시 노트를 삭제합니다.
    """
    try:
        # 1. 작성자 정보 구성
        author_user_ref = {"type": "HumanUser", "id": payload.author_id}

        # 2. 로컬 임시 노트 소유권 확인
        draft_note = db.query(database_models.Note).filter(database_models.Note.id == payload.draft_note_id).first()
        if not draft_note:
            raise HTTPException(status_code=404, detail=f"Draft note with id {payload.draft_note_id} not found.")
        if draft_note.owner_id != payload.author_id:
            raise HTTPException(status_code=403, detail="User is not the owner of the draft note.")

        # 3. ShotGrid에 노트 생성 및 첨부파일 업로드
        created_note = await shotgrid_api.async_api.create_shotgrid_note_with_attachments(
            sg=sg, payload=payload.model_dump(), author_user=author_user_ref
        )
        if not created_note:
            raise HTTPException(status_code=500, detail="Failed to create note in ShotGrid")

        # 4. 로컬 임시 노트 및 관련 데이터 삭제
        await draftnote_api.delete_draftnote_by_id(db=db, note_id=payload.draft_note_id, owner_id=payload.author_id)
        
        return {"detail": "Successfully published note to ShotGrid and deleted draft.", "shotgrid_note_id": created_note["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during the publish process: {str(e)}")

