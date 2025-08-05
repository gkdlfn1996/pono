
"""
PONO Backend Main Application File.
이 파일은 FastAPI 애플리케이션을 생성하고, 미들웨어와 API 라우터들을 연결합니다.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# routers 폴더에서 각 기능별 라우터를 가져옵니다.
from .routers import auth_router, notes_router, shotgrid_router

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="PONO Backend API",
    description="VFX Note-taking and collaboration tool backend.",
    version="0.1.0",
)

# CORS(Cross-Origin Resource Sharing) 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://30.0.1.141:8081", 
        "http://10.0.1.110:8081",
        "http://localhost:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 연결
app.include_router(auth_router.router)
app.include_router(notes_router.router)
app.include_router(shotgrid_router.router)

@app.get("/", tags=["Root"])
async def read_root():
    """
    루트 경로, API 서버가 정상적으로 동작하는지 확인합니다.
    """
    return {"message": "Welcome to PONO API"}
