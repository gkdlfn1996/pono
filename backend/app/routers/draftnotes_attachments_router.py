from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session # type: ignore
from typing import List # type: ignore
import os
import mimetypes

from ..draftnote import draftnote_api, draftnote_schema, database, database_models

router = APIRouter(
    prefix="/api",
    tags=["Attachments"],
)

@router.post("/versions/{version_id}/attachments", response_model=draftnote_schema.NoteInfo)
async def upload_attachments_for_version(
    version_id: int,
    files: List[UploadFile] = File([]),
    urls: List[str] = Form([]),
    owner_id: int = Form(...),
    db: Session = Depends(database.get_db),
):
    """
    특정 버전에 하나 이상의 파일을 첨부합니다. 노트가 없으면 자동 생성됩니다.
    """
    updated_note = await draftnote_api.create_attachments_for_version(
        db=db, version_id=version_id, files=files, urls=urls, owner_id=owner_id
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

@router.get("/attachments/{attachment_id}/{filename_for_browser}")
async def preview_attachment(
    attachment_id: int,
    filename_for_browser: str, # URL에 파일 이름을 포함시키기 위한 파라미터 (실제 로직에서는 사용되지 않음)
    db: Session = Depends(database.get_db),
):
    """
    ID를 기준으로 특정 첨부파일을 브라우저에서 미리보기로 엽니다.
    """
    attachment = db.query(database_models.Attachment).filter(database_models.Attachment.id == attachment_id).first()
    if not attachment or not os.path.exists(attachment.path_or_url) or attachment.file_type != 'file':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or not a previewable file")

    # 파일 확장자를 기반으로 MIME 타입 추론
    mime_type, _ = mimetypes.guess_type(attachment.path_or_url)
    # MIME 타입이 추론되지 않으면 기본값으로 application/octet-stream 사용
    return FileResponse(path=attachment.path_or_url, filename=attachment.file_name, media_type=mime_type or "application/octet-stream", content_disposition_type="inline")