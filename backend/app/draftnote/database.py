import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from . import database_models as models

# .env 파일에서 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 정보
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL)

# 세션 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 세션을 얻는 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===================================================================
# 데이터베이스 처리(CRUD) 함수 추가
# ===================================================================

# --- Version CRUD ---
def upsert_versions(db: Session, versions_meta: list[dict]):
    """
    버전 메타데이터 목록을 받아 `versions` 테이블에 대량으로 UPSERT합니다.
    """
    if not versions_meta:
        return
    
    stmt = pg_insert(models.Version).values(versions_meta)
    update_dict = {
        "name": stmt.excluded.name,
        "step_name": stmt.excluded.step_name,
        "project_id": stmt.excluded.project_id,
    }
    on_conflict_stmt = stmt.on_conflict_do_update(
        index_elements=['id'],
        set_=update_dict
    )
    db.execute(on_conflict_stmt)

# --- Note CRUD ---
def upsert_note(db: Session, note_data: dict, owner_id: int):
    """
    단일 노트 데이터를 받아 `notes` 테이블에 UPSERT합니다.
    """
    existing_note = db.query(models.Note).filter(
        models.Note.version_id == note_data['version_id'],
        models.Note.owner_id == owner_id
    ).first()

    if existing_note:
        existing_note.content = note_data['content']
        db.add(existing_note)
        return existing_note
    else:
        new_note = models.Note(**note_data, owner_id=owner_id)
        db.add(new_note)
        return new_note

def get_notes_by_step(db: Session, project_id: int, step_name: str):
    """
    프로젝트 ID와 스텝 이름을 기준으로, JOIN을 통해 모든 노트를 조회합니다.
    """
    query = db.query(models.Note).join(models.Version).filter(
        models.Version.project_id == project_id
    )

    # step_name이 'All'이 아닌 경우에만 스텝 필터를 추가합니다.
    if step_name != 'All':
        query = query.filter(models.Version.step_name == step_name)

    # updated_at 필드를 기준으로 내림차순(최신순)으로 정렬합니다.
    query = query.order_by(models.Note.updated_at.desc())

    return query.all()

def delete_note_by_versionid_ownerid(db: Session, version_id: int, owner_id: int):
    """
    주어진 version_id와 owner_id에 해당하는 노트가 있으면 삭제합니다.
    """
    note_to_delete = db.query(models.Note).filter(
        models.Note.version_id == version_id,
        models.Note.owner_id == owner_id
    ).first()

    if note_to_delete:
        db.delete(note_to_delete)
        return note_to_delete # 삭제 성공 시 Note 객체 반환
    return None # 삭제할 노트 없음

def delete_note_by_id(db: Session, note_id: int):
    """
    노트의 기본 키(id)를 기준으로 노트를 찾아 세션에서 삭제 대상으로 표시합니다.
    실제 삭제는 commit이 호출될 때 이루어집니다.
    """
    note_to_delete = db.query(models.Note).filter(models.Note.id == note_id).first()
    if note_to_delete:
        db.delete(note_to_delete)
        db.commit()
        return note_to_delete
    return None

