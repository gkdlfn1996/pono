# app/draftnote/websocket_manager.py

from fastapi import WebSocket
from typing import List

class ConnectionManager:
    """활성 WebSocket 연결을 관리하는 클래스입니다."""
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, version_id: int):
        """새로운 WebSocket 연결을 수락하고, 해당 버전 ID에 연결된 클라이언트 목록에 추가합니다."""
        await websocket.accept()
        if version_id not in self.active_connections:
            self.active_connections[version_id] = []
        self.active_connections[version_id].append(websocket)

    def disconnect(self, websocket: WebSocket, version_id: int):
        """WebSocket 연결을 해제하고, 해당 버전 ID의 클라이언트 목록에서 제거합니다."""
        if version_id in self.active_connections:
            self.active_connections[version_id].remove(websocket)
            if not self.active_connections[version_id]:
                del self.active_connections[version_id]

    async def broadcast(self, message: str, version_id: int):
        """특정 버전 ID에 연결된 모든 클라이언트에게 메시지를 브로드캐스트합니다."""
        if version_id in self.active_connections:
            for connection in self.active_connections[version_id]:
                await connection.send_text(message)
            print(f"[WebSocket] BROADCAST: message to version_id={version_id}, {len(self.active_connections[version_id])} clients.")

# 싱글턴 인스턴스로 생성하여 앱 전체에서 공유
manager = ConnectionManager()
