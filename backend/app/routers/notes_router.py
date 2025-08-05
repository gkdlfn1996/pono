
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter(
    prefix="/api/notes",
    tags=["Notes & WebSocket"],
)

class ConnectionManager:
    """
    활성 WebSocket 연결을 관리하는 클래스입니다.
    버전 ID별로 연결을 그룹화하여 특정 버전의 클라이언트에게 메시지를 보낼 수 있습니다.
    """
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, version_id: int):
        await websocket.accept()
        if version_id not in self.active_connections:
            self.active_connections[version_id] = []
        self.active_connections[version_id].append(websocket)
        print(f"WebSocket connected: version_id={version_id}, total: {len(self.active_connections[version_id])}")

    def disconnect(self, websocket: WebSocket, version_id: int):
        if version_id in self.active_connections:
            self.active_connections[version_id].remove(websocket)
            if not self.active_connections[version_id]:
                del self.active_connections[version_id]
        print(f"WebSocket disconnected: version_id={version_id}")

    async def broadcast(self, message: str, version_id: int, exclude_websocket: WebSocket = None):
        if version_id in self.active_connections:
            for connection in self.active_connections[version_id]:
                if connection != exclude_websocket:
                    await connection.send_text(message)
            print(f"Broadcasted to version {version_id}: {message}")

manager = ConnectionManager()

@router.websocket("/ws/{version_id}")
async def websocket_endpoint(websocket: WebSocket, version_id: int):
    """
    버전 ID별로 WebSocket 연결을 처리하는 엔드포인트입니다.
    """
    await manager.connect(websocket, version_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 클라이언트로부터 받은 메시지를 다른 클라이언트에게 브로드캐스트합니다.
            # 메시지를 보낸 클라이언트는 제외합니다.
            await manager.broadcast(f"Client #{version_id} says: {data}", version_id, exclude_websocket=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, version_id)
        await manager.broadcast(f"Client #{version_id} left the chat", version_id)
