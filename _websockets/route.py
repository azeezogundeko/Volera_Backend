import uuid
from typing import Optional

from .connection_manager import manager
from .message_handler import handle_message
from utils.logging import logger

from fastapi import WebSocket, WebSocketDisconnect, APIRouter

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, path: Optional[str] = None):
    """
    WebSocket endpoint that uses the ConnectionManager to manage connections.

    Args:
        websocket (WebSocket): WebSocket connection instance.
        path (Optional[str]): Optional path query parameters.
    """
    await manager.connect(websocket)
    
    # Generate a unique user ID for this connection
    user_id = str(uuid.uuid4())
    
    try:
        logger.info("Websocket Server is runing")
        while True:
            # Receive text message
            data = await websocket.receive_text()
            
            # Handle the message using the message handler
            await handle_message(data, websocket, user_id)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
