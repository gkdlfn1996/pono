"""
draftnote.models 모듈

이 모듈은 PostgreSQL 데이터베이스에 저장될 임시 노트 및 사용자 정보의
데이터베이스 스키마(테이블 구조)를 정의합니다. SQLAlchemy의 ORM(Object-Relational Mapping)을
사용하여 파이썬 클래스를 데이터베이스 테이블에 매핑합니다.

주요 기능:
- `Base`: SQLAlchemy ORM의 선언적 기본 클래스입니다.
- `User`: 사용자 정보를 나타내는 데이터베이스 모델입니다.
- `Note`: 임시 노트의 내용을 나타내는 데이터베이스 모델입니다. 특정 버전, 소유자, 내용, 생성 및 업데이트 시간을 포함합니다.
- `Attachment`: 노트에 첨부된 파일 또는 링크 정보를 나타내는 데이터베이스 모델입니다.

사용 방법:
- 이 모델들은 데이터베이스 테이블을 생성하고, 데이터를 조회, 삽입, 수정, 삭제하는 데 사용됩니다.
- FastAPI 애플리케이션 시작 시 `Base.metadata.create_all(bind=engine)`을 호출하여
  데이터베이스에 테이블을 생성할 수 있습니다.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    login = Column(String, unique=True, index=True)
    notes = relationship("Note", back_populates="owner")
    attachments = relationship("Attachment", back_populates="owner")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    version_id = Column(Integer, ForeignKey("versions.id"), index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    owner = relationship("User", back_populates="notes")
    version = relationship("Version", back_populates="notes")
    attachments = relationship("Attachment", back_populates="note", cascade="all, delete-orphan")

class Version(Base):
    __tablename__ = "versions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    step_name = Column(String, index=True)
    project_id = Column(Integer, index=True)
    notes = relationship("Note", back_populates="version")

class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True, index=True)
    path_or_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    note = relationship("Note", back_populates="attachments")
    owner = relationship("User", back_populates="attachments")
