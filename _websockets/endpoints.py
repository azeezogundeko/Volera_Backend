from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Optional
from connection_manager import ConnectionManager  # Import your class

app = FastAPI()

# Initialize the connection manager
manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, path: Optional[str] = None):
    """
    WebSocket endpoint that uses the ConnectionManager to manage connections.

    Args:
        websocket (WebSocket): WebSocket connection instance.
        path (Optional[str]): Optional path query parameters.
    """
    await manager.handle_connection(websocket, path)
