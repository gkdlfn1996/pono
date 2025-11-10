"""
PONO Backend Main Application File.
이 파일은 FastAPI 애플리케이션을 생성하고, 미들웨어와 API 라우터들을 연결합니다.
"""
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import text
from .draftnote.database import engine
from .draftnote.database_models import Base
from fastapi.middleware.cors import CORSMiddleware
from shotgun_api3.shotgun import AuthenticationFault
from .shotgrid.shotgrid_authenticator import authentication_fault_handler
import logging
import logging.config
from log_config import LOGGING_CONFIG

FRONTEND_PORT=int(os.getenv('FRONTEND_PORT'))

# 커스텀 로그 설정
logging.config.dictConfig(LOGGING_CONFIG)

# routers 폴더에서 각 기능별 라우터를 가져옵니다.
from .routers import auth_router, draftnotes_router, shotgrid_data_router, draftnotes_attachments_router, shotgrid_publish_router, utils_router

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="PONO Backend API",
    description="VFX Note-taking and collaboration tool backend.",
    version="0.1.0",
)

# 전역 예외 처리기 등록
app.add_exception_handler(AuthenticationFault, authentication_fault_handler)

# 데이터베이스 테이블 생성
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

# 정적 파일 경로 마운트 (이미지 등)
# /static/docs URL을 docs 디렉토리에 연결
app.mount("/static/docs", StaticFiles(directory="../docs"), name="static_docs")


# API 라우터 연결
app.include_router(auth_router.router)
app.include_router(draftnotes_router.router)
app.include_router(shotgrid_data_router.router)
app.include_router(draftnotes_attachments_router.router)
app.include_router(shotgrid_publish_router.router)
app.include_router(utils_router.router, prefix="/api/utils", tags=["utils"])

# 서버 시작 시 첨부파일 기본 디렉토리 보장
@app.on_event("startup")
def ensure_attachment_dir():
    """서버 시작 시 사용자 홈 디렉토리에 첨부파일 기본 저장 폴더를 자동 생성합니다."""
    attachment_base_path = Path.home() / "pono_attachments"
    os.makedirs(attachment_base_path, exist_ok=True)
    print(f"[startup] Ensured attachment base directory: {attachment_base_path}")