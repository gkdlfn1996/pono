# app/draftnote/draftnote_schema.py

from pydantic import BaseModel
from typing import List
from datetime import datetime

# --- User Schemas ---
class UserInfo(BaseModel):
    """노트 소유자의 기본 정보를 나타내는 Pydantic 모델입니다."""
    id: int
    username: str
    login: str

    class Config:
        from_attributes = True

# --- Version Schemas ---
class VersionMeta(BaseModel):
    """노트 저장 시 함께 받을 버전 메타데이터 모델"""
    id: int
    name: str
    step_name: str
    project_id: int

# --- Attachment Schemas ---
class AttachmentInfo(BaseModel):
    """클라이언트에 반환될 첨부파일 정보 모델"""
    id: int
    attachment_type: str
    path_or_url: str
    original_filename: str | None = None

    class Config:
        from_attributes = True

# --- Note Schemas ---
class NoteBase(BaseModel):
    """노트의 기본 내용을 정의하는 Pydantic 모델입니다."""
    content: str

class NoteCreate(NoteBase):
    """새 노트를 생성하거나 업데이트할 때 사용되는 Pydantic 모델입니다."""
    version_id: int
    owner_id: int
    version_meta: VersionMeta

class NoteInfo(BaseModel):
    """클라이언트에 반환될 노트의 상세 정보를 나타내는 Pydantic 모델입니다."""
    id: int
    version_id: int
    content: str
    updated_at: datetime
    owner: UserInfo
    attachments: List[AttachmentInfo] = []

    class Config:
        from_attributes = True
