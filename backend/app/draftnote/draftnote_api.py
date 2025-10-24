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
            shutil.rmtree(folder_path)
            print(f"첨부파일 폴더 삭제 완료: {folder_path}")
        except OSError as e:
            print(f"첨부파일 폴더 삭제 실패 {folder_path}: {e}")

async def _broadcast_note_update(note: models.Note, db: Session):
    """헬퍼 함수: 노트 정보를 웹소켓으로 브로드캐스트합니다."""
    note_info = schemas.NoteInfo.model_validate(note)
    await websocket_manager.manager.broadcast(note_info.model_dump_json(), note.version_id)

async def _broadcast_note_deletion(version_id: int, owner_id: int, db: Session):
    """헬퍼 함수: 노트 삭제 정보를 웹소켓으로 브로드캐스트합니다."""
    user = db.query(models.User).filter(models.User.id == owner_id).first()
    owner_info = schemas.UserInfo.model_validate(user) if user else schemas.UserInfo(id=owner_id, username="", login="")
    empty_note_info = schemas.NoteInfo(
        id=0,
        version_id=version_id,
        content="",
        owner=owner_info,
        attachments=[],
        updated_at=datetime.now()
    )
    await websocket_manager.manager.broadcast(empty_note_info.model_dump_json(), version_id)


async def save_note_logic(note_data: schemas.NoteCreate, db: Session):
    """
    노트 '내용' 생성/업데이트/삭제와 웹소켓 브로드캐스트까지의 로직을 처리합니다.
    """
    try:
        # 1. 내용이 비어있는 경우의 처리
        if not note_data.content.strip():
            note_to_process = db.query(models.Note).filter(
                models.Note.version_id == note_data.version_id,
                models.Note.owner_id == note_data.owner_id
            ).first()

            if note_to_process:
                # 시나리오 B: 첨부파일 유무에 따른 분기 처리
                if note_to_process.attachments:
                    # 첨부파일이 있으면 내용만 비움 (노트 업데이트)
                    note_to_process.content = ""
                    db.commit()
                    db.refresh(note_to_process)
                    await _broadcast_note_update(note_to_process, db)
                    return note_to_process
                else:
                    # 첨부파일이 없으면 노트 전체 삭제
                    deleted_note = database.delete_note_by_versionid_ownerid(db, note_data.version_id, note_data.owner_id)
                    if deleted_note:
                        await _delete_attachments_folder(deleted_note.id, deleted_note.owner_id)
                        db.commit()
                        await _broadcast_note_deletion(note_data.version_id, note_data.owner_id, db)
            
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

            # 3. 웹소켓 브로드캐스트
            await _broadcast_note_update(saved_note, db)
            return saved_note

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def create_attachments_for_version(db: Session, version_id: int, files: List[UploadFile], urls: List[str], owner_id: int):
    """
    version_id를 기준으로 노트를 찾거나 생성한 후, 파일을 첨부합니다.
    """
    # 1. version_id와 owner_id로 기존 노트가 있는지 확인
    note = db.query(models.Note).filter(
        models.Note.version_id == version_id,
        models.Note.owner_id == owner_id
    ).first()

    # 2. 노트가 없으면, 빈 내용으로 새로 생성
    if not note:
        note_data = {"version_id": version_id, "content": ""}
        note = database.upsert_note(db, note_data, owner_id)
        db.commit()
        db.refresh(note)

    # 3. 기존 첨부파일 추가 로직 실행
    save_dir = Path.home() / 'pono_attachments' / str(note.id) / str(owner_id)
    os.makedirs(save_dir, exist_ok=True)

    for file in files:
        unique_id = uuid.uuid4()
        file_extension = os.path.splitext(file.filename)[1]
        saved_filename = f"{unique_id}{file_extension}"
        file_path = save_dir / saved_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_attachment = models.Attachment(note_id=note.id, owner_id=owner_id, file_type='file', path_or_url=str(file_path), file_name=file.filename)
        db.add(new_attachment)
    
    for url_str in urls:
        new_attachment = models.Attachment(note_id=note.id, owner_id=owner_id, file_type='url', path_or_url=url_str, file_name=None)
        db.add(new_attachment)

    db.commit()
    db.refresh(note)
    await _broadcast_note_update(note, db)
    return note

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

    note = attachment.note
    version_id_for_signal = note.version_id

    # attachment_type이 'file'인 경우, 물리적 파일 삭제
    if attachment.file_type == 'file' and os.path.exists(attachment.path_or_url):
        os.remove(attachment.path_or_url)

    # DB에서 첨부파일 레코드 삭제
    db.delete(attachment)
    db.commit()

    # 첨부파일 삭제 후 노트 상태를 다시 읽어옴
    db.refresh(note)

    # 이제 노트가 비었는지 (내용도, 첨부파일도 없는지) 확인
    if not note.content.strip() and not note.attachments:
        # 비었다면, 노트 자체와 관련 폴더를 삭제
        await _delete_attachments_folder(note.id, note.owner_id)
        db.delete(note)
        db.commit()

        await _broadcast_note_deletion(version_id_for_signal, owner_id, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        # 노트가 비어있지 않다면, 그냥 업데이트된 노트 정보를 방송
        await _broadcast_note_update(note, db)
        return note 

async def delete_draftnote_by_id(db: Session, note_id: int, owner_id: int):
    """
    ID를 기준으로 임시 노트를 찾아서, 노트와 모든 종속 항목(첨부파일 폴더)을 삭제하고,
    웹소켓으로 삭제 신호를 전파합니다.
    - Args:
        - db (Session): 데이터베이스 세션.
        - note_id (int): 삭제할 노트의 ID.
        - owner_id (int): API를 요청한 사용자의 ID (권한 확인용).
    """
    # 1. 노트 조회 및 소유권 확인
    print('------------------')
    print(f'note_id:{note_id}, owner_id:{owner_id}')
    note_to_delete = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note_to_delete:
        # 노트가 이미 다른 프로세스에 의해 삭제되었을 수 있으므로, 오류 대신 조용히 종료합니다.
        print(f"Note with id {note_id} not found. It might have been already deleted.")
        return
    if note_to_delete.owner_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this note")

    version_id_for_signal = note_to_delete.version_id

    # 2. DB 삭제 로직을 database.py에 위임 (내부에서 commit 및 print 실행)
    deleted_note_from_db = database.delete_note_by_id(db, note_id)

    # 3. DB 삭제가 성공적으로 이루어졌다면 후속 작업 진행
    if deleted_note_from_db:
        # 4. 물리적 첨부파일 폴더 삭제
        await _delete_attachments_folder(note_id, owner_id)
        # 5. 웹소켓으로 삭제 신호 전파
        await _broadcast_note_deletion(version_id_for_signal, owner_id, db)