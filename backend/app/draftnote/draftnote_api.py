# app/draftnote/draftnote_api.py
from fastapi import HTTPException, Response, status, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from pathlib import Path
import os
import asyncio
import uuid
import shutil

from . import draftnote_schema as schemas
from . import database
from . import websocket_manager
from . import database_models as models

async def _delete_attachments_folder(note_id: int, owner_id: int):
    """
    특정 노트와 소유자에 해당하는 첨부파일 폴더를 재귀적으로 삭제합니다.
    """
    folder_path = Path.home() / 'pono_attachments' / str(note_id) / str(owner_id)
    if folder_path.exists() and folder_path.is_dir():
        try:
            # shutil.rmtree는 동기 함수이므로, 비동기 컨텍스트에서 실행하기 위해 run_in_threadpool 사용
            # 하지만 여기서는 간단히 os.system을 사용하거나,
            # FastAPI의 run_in_threadpool을 사용해야 하지만, 현재 파일에서는 직접 임포트하지 않음.
            # 따라서, 여기서는 동기 함수를 직접 호출하는 것으로 작성하고, 필요시 리팩토링.
            shutil.rmtree(folder_path)
            print(f"첨부파일 폴더 삭제 완료: {folder_path}")
        except OSError as e:
            print(f"첨부파일 폴더 삭제 실패 {folder_path}: {e}")

async def save_note_logic(note_data: schemas.NoteCreate, db: Session):
    """
    노트 '내용' 생성/업데이트/삭제와 웹소켓 브로드캐스트까지의 로직을 처리합니다.
    """
    try:
        # 1. 내용이 비어있으면 노트 삭제
        if not note_data.content.strip():
            deleted_note = database.delete_note_if_exists(db, note_data.version_id, note_data.owner_id)
            if deleted_note:
                db.commit()
                # 노트 삭제 시, 해당 노트의 첨부파일 폴더도 함께 삭제
                await _delete_attachments_folder(deleted_note.id, deleted_note.owner_id)
                # 삭제 후에는 DB를 건드리지 않고 수동으로 빈 노트를 생성하여 방송
                user = db.query(models.User).filter(models.User.id == note_data.owner_id).first()
                owner_info = schemas.UserInfo.model_validate(user) if user else schemas.UserInfo(id=note_data.owner_id, username="", login="")
                empty_note_info = schemas.NoteInfo(id=0, version_id=note_data.version_id, content="", owner=owner_info, attachments=[], updated_at=datetime.now())
                await websocket_manager.manager.broadcast(empty_note_info.model_dump_json(), note_data.version_id)
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
            # 저장 후에는 DB에서 가져온 객체를 validate하여 방송
            note_info = schemas.NoteInfo.model_validate(saved_note)
            await websocket_manager.manager.broadcast(note_info.model_dump_json(), saved_note.version_id)
            return note_info

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
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
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
        new_attachment = models.Attachment(
            note_id=note_id,
            owner_id=owner_id,
            file_type='file',
            path_or_url=str(file_path), # pathlib 객체를 문자열로 변환하여 저장
            file_name=file.filename
        )
        db.add(new_attachment)
    
    db.commit()
    db.refresh(note) # 첨부파일이 추가된 최신 상태를 DB로부터 다시 읽어옴
    note_info = schemas.NoteInfo.model_validate(note)
    await websocket_manager.manager.broadcast(note_info.model_dump_json(), note.version_id)
    return note_info

async def delete_attachment_by_id(db: Session, attachment_id: int, owner_id: int):
    """
    ID를 기준으로 특정 첨부파일을 삭제하고, 변경사항을 브로드캐스트합니다.

    - Args:
        - db (Session): 데이터베이스 세션.
        - attachment_id (int): 삭제할 첨부파일의 ID.
        - owner_id (int): API를 요청한 사용자의 ID (권한 확인용).
    """
    attachment = db.query(models.Attachment).filter(models.Attachment.id == attachment_id).first()
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
    db.refresh(note) # 첨부파일이 삭제된 최신 상태를 DB로부터 다시 읽어옴

    # 해당 노트에 더 이상 첨부파일이 없으면 폴더도 삭제
    if not note.attachments:
        await _delete_attachments_folder(note.id, note.owner_id)

    note_info = schemas.NoteInfo.model_validate(note)
    await websocket_manager.manager.broadcast(note_info.model_dump_json(), note.version_id)
    return note_info
