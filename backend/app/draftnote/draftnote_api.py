# app/draftnote/draftnote_api.py
from fastapi import HTTPException, Response, status, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from pathlib import Path
import os
import uuid
import shutil

from . import draftnote_schema as schemas
from . import database
from . import websocket_manager

async def save_note_logic(note_data: schemas.NoteCreate, db: Session):
    """
    노트 '내용' 생성/업데이트/삭제와 웹소켓 브로드캐스트까지의 로직을 처리합니다.
    """
    try:
        # 1. 내용이 비어있으면 노트 삭제
        if not note_data.content.strip():
            was_deleted = database.delete_note_if_exists(db, note_data.version_id, note_data.owner_id)
            if was_deleted:
                db.commit()
                # 노트 자체가 삭제되었으므로, 해당 노트 정보를 다시 조회하여 브로드캐스트
                await broadcast_note_update(db, note_data.version_id, note_data.owner_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        
        # 2. 내용이 있으면 노트 저장/업데이트
        else:
            # 버전 정보 UPSERT
            database.upsert_versions(db, [note_data.version_meta.model_dump()])
            
            # 노트 정보 UPSERT
            note_to_save = {"version_id": note_data.version_id, "content": note_data.content}
            saved_note = database.upsert_note(db, note_to_save, note_data.owner_id)
            
            db.commit()
            db.refresh(saved_note)

            # 3. 웹소켓 브로드캐스트 (첨부파일 포함 최신 정보)
            await broadcast_note_update(db, saved_note.version_id, saved_note.owner_id)
            return db.query(database.models.Note).filter(database.models.Note.id == saved_note.id).first()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def create_attachments_for_note(db: Session, note_id: int, files: List[UploadFile], owner_id: int):
    """
    특정 노트에 하나 이상의 파일을 첨부하고, 변경사항을 브로드캐스트합니다.
    note_id/owner_id 구조의 하위 디렉토리를 동적으로 생성합니다.

    - Args:
        - db (Session): 데이터베이스 세션.
        - note_id (int): 파일이 첨부될 노트의 ID.
        - files (List[UploadFile]): 업로드된 파일 객체 리스트.
        - owner_id (int): API를 요청한 사용자의 ID.
    """
    note = db.query(database.models.Note).filter(database.models.Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add attachments to this note")

    # 저장 경로 구성: /home/idea/pono_attachments/{note_id}/{owner_id}
    save_dir = Path.home() / 'pono_attachments' / str(note_id) / str(owner_id)
    os.makedirs(save_dir, exist_ok=True)

    for file in files:
        # 고유한 파일명 생성 (UUID 사용)
        unique_id = uuid.uuid4()
        file_extension = os.path.splitext(file.filename)[1]
        saved_filename = f"{unique_id}{file_extension}"
        file_path = save_dir / saved_filename

        # 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # DB에 Attachment 레코드 생성
        new_attachment = database.models.Attachment(
            note_id=note_id,
            owner_id=owner_id,
            file_type='file',
            path_or_url=str(file_path), # pathlib 객체를 문자열로 변환하여 저장
            file_name=file.filename
        )
        db.add(new_attachment)
    
    db.commit()
    await broadcast_note_update(db, note.version_id, note.owner_id)
    return note

async def delete_attachment_by_id(db: Session, attachment_id: int, owner_id: int):
    """
    ID를 기준으로 특정 첨부파일을 삭제하고, 변경사항을 브로드캐스트합니다.

    - Args:
        - db (Session): 데이터베이스 세션.
        - attachment_id (int): 삭제할 첨부파일의 ID.
        - owner_id (int): API를 요청한 사용자의 ID (권한 확인용).
    """
    attachment = db.query(database.models.Attachment).filter(database.models.Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    if attachment.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this attachment")

    note = attachment.note # 브로드캐스트를 위해 부모 노트를 미리 가져옴

    # attachment_type이 'file'인 경우, 물리적 파일 삭제
    if attachment.file_type == 'file':
        if os.path.exists(attachment.path_or_url):
            os.remove(attachment.path_or_url)

    db.delete(attachment)
    db.commit()
    await broadcast_note_update(db, note.version_id, note.owner_id)
    return note

async def broadcast_note_update(db: Session, version_id: int, owner_id: int):
    """
    특정 노트의 최신 정보를 조회하여 웹소켓으로 브로드캐스트합니다.
    노트가 존재하지 않는 경우(삭제된 경우), 빈 노트 정보를 보냅니다.
    """
    updated_note = db.query(database.models.Note).filter(database.models.Note.version_id == version_id, database.models.Note.owner_id == owner_id).first()
    note_info = schemas.NoteInfo.model_validate(updated_note) if updated_note else None
    
    # 노트가 삭제된 경우를 대비하여, 빈 노트 정보를 보낼 수도 있음
    if not note_info:
        user = db.query(database.models.User).filter(database.models.User.id == owner_id).first()
        note_info = schemas.NoteInfo(id=0, version_id=version_id, content="", owner=user, attachments=[])

    await websocket_manager.manager.broadcast(note_info.model_dump_json(), version_id)