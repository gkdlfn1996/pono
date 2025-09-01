"""
draftnote.models 모듈

이 모듈은 PostgreSQL 데이터베이스에 저장될 임시 노트 및 사용자 정보의
데이터베이스 스키마(테이블 구조)를 정의합니다. SQLAlchemy의 ORM(Object-Relational Mapping)을
사용하여 파이썬 클래스를 데이터베이스 테이블에 매핑합니다.

주요 기능:
- `Base`: SQLAlchemy ORM의 선언적 기본 클래스입니다.
- `User`: 사용자 정보를 나타내는 데이터베이스 모델입니다. ShotGrid 사용자 이름과 연결됩니다.
- `Note`: 임시 노트의 내용을 나타내는 데이터베이스 모델입니다. 특정 버전, 소유자, 내용,
  생성 및 업데이트 시간을 포함합니다.

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
    """
    사용자 정보를 나타내는 SQLAlchemy 모델입니다.
    ShotGrid 사용자 이름과 연결되며, 사용자가 작성한 노트들과 관계를 맺습니다.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # ShotGrid 사용자 이름

    notes = relationship("Note", back_populates="owner")

class Note(Base):
    """
    임시 노트의 내용을 나타내는 SQLAlchemy 모델입니다.
    특정 ShotGrid 버전, 노트 소유자, 내용, 생성 및 업데이트 시간을 저장합니다.
    """
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, index=True) # ShotGrid 버전 ID (예: sg_version_id)
    owner_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="notes")
