# app/draftnote/draftnote_api.py

from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session
from datetime import datetime

from . import draftnote_schema as schemas
from . import database
from . import websocket_manager

async def save_note_logic(note_data: schemas.NoteCreate, db: Session):
    """
    노트 생성/업데이트/삭제와 웹소켓 브로드캐스트까지의 전체 비즈니스 로직을 처리합니다.
    """
    try:
        # 1. 내용이 비어있으면 노트 삭제
        if not note_data.content.strip():
            was_deleted = database.delete_note_if_exists(db, note_data.version_id, note_data.owner_id)
            if was_deleted:
                db.commit()
                # 삭제 성공 시, 다른 사용자에게 빈 내용의 노트를 보내 삭제되었음을 알림
                note_info_for_broadcast = schemas.NoteInfo(
                    id=0, version_id=note_data.version_id, content="", 
                    updated_at=datetime.now(), 
                    owner=schemas.UserInfo(id=note_data.owner_id, username="", login="")
                )
                await websocket_manager.manager.broadcast(note_info_for_broadcast.model_dump_json(), note_data.version_id)
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
            note_info_for_broadcast = schemas.NoteInfo.model_validate(saved_note)
            await websocket_manager.manager.broadcast(note_info_for_broadcast.model_dump_json(), saved_note.version_id)
            
            return note_info_for_broadcast

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


