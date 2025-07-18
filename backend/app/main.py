import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from . import models
from contextlib import asynccontextmanager
from . import router
import json


# Lifespan 이벤트 핸들러 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    from .database import engine
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

# CORS 설정: 프론트엔드( localhost:8080 )에서 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 포함
app.include_router(router.router)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        # Dictionary to hold active connections, grouped by version_id
        # { version_id: [websocket1, websocket2, ...] }
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, version_id: int):
        await websocket.accept()
        if version_id not in self.active_connections:
            self.active_connections[version_id] = []
        self.active_connections[version_id].append(websocket)
        print(f"WebSocket connected: version_id={version_id}, total connections for this version: {len(self.active_connections[version_id])})")

    def disconnect(self, websocket: WebSocket, version_id: int):
        if version_id in self.active_connections:
            self.active_connections[version_id].remove(websocket)
            if not self.active_connections[version_id]: # If no connections left for this version
                del self.active_connections[version_id]
        print(f"WebSocket disconnected: version_id={version_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, version_id: int, exclude_websocket: WebSocket = None):
        if version_id in self.active_connections:
            for connection in self.active_connections[version_id]:
                if connection != exclude_websocket: # Don't send back to the sender
                    await connection.send_text(message)
            print(f"Broadcasted message to version {version_id}: {message}")

manager = ConnectionManager()

@app.websocket("/ws/{version_id}")
async def websocket_endpoint(websocket: WebSocket, version_id: int):
    await manager.connect(websocket, version_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message from version {version_id}: {data}")
            await manager.broadcast(data, version_id, exclude_websocket=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, version_id)
        print(f"Client disconnected from version {version_id}")
    except Exception as e:
        print(f"WebSocket error for version {version_id}: {e}")
        manager.disconnect(websocket, version_id)
