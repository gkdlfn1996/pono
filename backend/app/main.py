from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정: 프론트엔드( localhost:8080 )에서 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        print(f"Disconnecting: Checking version_id {version_id}")
        if version_id in self.active_connections:
            print(f"Disconnecting: version_id {version_id} found. Removing websocket.")
            self.active_connections[version_id].remove(websocket)
            print(f"Disconnecting: Websocket removed. Checking if list is empty.")
            if not self.active_connections[version_id]: # If no connections left for this version
                print(f"Disconnecting: No connections left for version {version_id}. Deleting key.")
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