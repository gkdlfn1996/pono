from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

from ..draftnote import draftnote_api, draftnote_schema, database, database_models

router = APIRouter(
    prefix="/api",
    tags=["Attachments"],
)

@router.post("/notes/{note_id}/attachments", response_model=draftnote_schema.NoteInfo)
async def upload_attachments_for_note(
    note_id: int,
    files: List[UploadFile] = File(...),
    owner_id: int = Form(...),
    db: Session = Depends(database.get_db),
):
    """
    특정 노트에 하나 이상의 파일을 첨부합니다.
    """
    updated_note = await draftnote_api.create_attachments_for_note(
        db=db, note_id=note_id, files=files, owner_id=owner_id
    )
    return updated_note

@router.delete("/attachments/{attachment_id}", response_model=draftnote_schema.NoteInfo)
async def delete_attachment(
    attachment_id: int,
    owner_id: int, # 쿼리 파라미터로 owner_id를 받습니다.
    db: Session = Depends(database.get_db),
):
    """
    특정 첨부파일을 삭제합니다.
    """
    updated_note = await draftnote_api.delete_attachment_by_id(
        db=db, attachment_id=attachment_id, owner_id=owner_id
    )
    return updated_note

@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    db: Session = Depends(database.get_db),
):
    """
    ID를 기준으로 특정 첨부파일을 다운로드합니다.
    """
    attachment = db.query(database_models.Attachment).filter(database_models.Attachment.id == attachment_id).first()
    if not attachment or not os.path.exists(attachment.path_or_url):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(path=attachment.path_or_url, filename=attachment.file_name)