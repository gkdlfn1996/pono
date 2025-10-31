"""
PONO Backend Main Application File.
이 파일은 FastAPI 애플리케이션을 생성하고, 미들웨어와 API 라우터들을 연결합니다.
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import text
from .draftnote.database import engine
from .draftnote.database_models import Base
from fastapi.middleware.cors import CORSMiddleware
from shotgun_api3.shotgun import AuthenticationFault
from .shotgrid.shotgrid_authenticator import authentication_fault_handler

# .env 파일 로드
load_dotenv()
FRONTEND_PORT=int(os.getenv('FRONTEND_PORT'))

# routers 폴더에서 각 기능별 라우터를 가져옵니다.
from .routers import auth_router, draftnotes_router, shotgrid_data_router, draftnotes_attachments_router
from .routers import shotgrid_publish_router

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="PONO Backend API",
    description="VFX Note-taking and collaboration tool backend.",
    version="0.1.0",
)

# 전역 예외 처리기 등록
app.add_exception_handler(AuthenticationFault, authentication_fault_handler)

# 데이터베이스 테이블 생성
# 애플리케이션 시작 시 draftnote/models.py에 정의된 모든 테이블을 데이터베이스에 생성합니다.
# 개발 단계에서 테이블 스키마 변경 시 유용하며, 운영 환경에서는 마이그레이션 도구를 사용하는 것이 일반적입니다.
Base.metadata.create_all(bind=engine)


# CORS(Cross-Origin Resource Sharing) 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://30.0.1.141:{FRONTEND_PORT}", 
        f"http://10.0.1.110:{FRONTEND_PORT}",
        f"http://localhost:{FRONTEND_PORT}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 연결
app.include_router(auth_router.router)
app.include_router(draftnotes_router.router)
app.include_router(shotgrid_data_router.router)
app.include_router(draftnotes_attachments_router.router)
app.include_router(shotgrid_publish_router.router)