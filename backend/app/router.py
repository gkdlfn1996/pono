from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel # EchoRequest를 위해 추가
from typing import Optional
from .database import get_db # 상위 폴더의 database.py에서 get_db 임포트
from .shotgrid_client import ShotGridClient # sg_client 사용을 위해 추가

router = APIRouter()
sg_client = ShotGridClient() # 라우터 파일에서 sg_client 초기화

class EchoRequest(BaseModel):
    text: str

class LoginRequest(BaseModel):
    username: str
    password: str

class NoteBase(BaseModel):
    content: str

class NoteCreate(NoteBase):
    version_id: int # ShotGrid 버전 ID
    owner_id: int # 사용자 ID (우리 DB의 users.id)

class NoteUpdate(BaseModel):
    content: str # 업데이트할 내용

# 다른 사용자 노트를 반환하기 위한 Pydantic 모델
class UserInfo(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class NoteInfo(BaseModel):
    id: int
    content: str
    updated_at: datetime
    owner: UserInfo

    class Config:
        orm_mode = True

@router.post("/api/echo")
def echo(req: EchoRequest):
    return {"echo": req.text}

@router.get("/api/project/{project_name}/shots")
def project_shots(project_name: str):
    project = sg_client.get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    shots = sg_client.get_shots(project.get("id"))
    return {"shots": shots}

@router.get("/api/projects")
def project_list():
    """
    프로젝트 이름 목록을 반환합니다。
    """
    projects = sg_client.get_projects()
    return {"projects": projects}

@router.get("/api/shot/{shot_id}/versions")
def shot_versions(shot_id: int):
    """
    특정 Shot의 버전 목록을 반환합니다。
    """
    versions = sg_client.get_versions_for_shot(shot_id)
    return {"versions": versions}

#---------------------------------------- Login -----------------------------------------------

@router.post("/api/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    print(f"Login attempt for username: {request.username}")
    print("Calling ShotGrid authentication...")
    user_info = sg_client.authenticate_human_user(request.username, request.password)
    print(f"ShotGrid authentication result: {user_info}")
    if user_info:
        print(f"User '{user_info['login']}' authenticated with ShotGrid. Checking local DB...")
        from . import models # models.py 임포트 (함수 내에서 필요시)

        # 로컬 DB에 사용자 정보 저장 또는 조회
        user = db.query(models.User).filter(models.User.username == user_info["login"]).first()
        print(f"Local DB user query result: {user}")
        if not user:
            # 사용자가 없으면 새로 생성
            print(f"User '{user_info['login']}' not found in local DB. Creating new user...")
            user = models.User(username=user_info["login"])
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"New user created with ID: {user.id}")
        return {"message": "Login successful", "user": {"id": user.id, "name": user_info["name"]}}
    else:
        print("ShotGrid authentication failed. Returning 401.")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/api/notes")
def create_or_update_note(
    note_data: NoteCreate, # 노트 생성/업데이트 데이터
    db: Session = Depends(get_db)
):
    from . import models # models.py 임포트

    # 기존 노트가 있는지 확인 (version_id와 owner_id로)
    existing_note = db.query(models.Note).filter(
        models.Note.version_id == note_data.version_id,
        models.Note.owner_id == note_data.owner_id
    ).first()

    if existing_note:
        # 노트가 존재하면 업데이트
        existing_note.content = note_data.content
        db.add(existing_note)
        db.commit()
        db.refresh(existing_note)
        return {"message": "Note updated successfully", "note": existing_note}
    else:
        # 노트가 없으면 새로 생성
        new_note = models.Note(**note_data.dict())
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        return {"message": "Note created successfully", "note": new_note}

@router.get("/api/notes/{version_id}/{owner_id}")
def get_note(version_id: int, owner_id: int, db: Session = Depends(get_db)):
    from . import models # models.py 임포트

    note = db.query(models.Note).filter(
        models.Note.version_id == version_id,
        models.Note.owner_id == owner_id
    ).first()
    if note:
        return {"note": note}
    raise HTTPException(status_code=404, detail="Note not found")

@router.get("/api/notes/{version_id}", response_model=list[NoteInfo])
def get_notes_for_version(version_id: int, db: Session = Depends(get_db)):
    """특정 버전에 달린 모든 노트를 작성자 정보와 함께 반환합니다."""
    from . import models # models.py 임포트

    notes = db.query(models.Note).filter(models.Note.version_id == version_id).all()
    if not notes:
        return [] # 노트가 없으면 빈 리스트 반환

    # response_model에 맞게 데이터 구조를 변환하여 반환
    return notes

# ---------------------------------------- TEST -----------------------------------------------

@router.get("/db-test")
async def db_test(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            return {"message": "Database connection successful!"}
        else:
            return {"message": "Database connection failed: Unexpected result."}
    except Exception as e:
        return {"message": f"Database connection failed: {e}"}