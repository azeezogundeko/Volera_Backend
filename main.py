from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Optional
import uvicorn
from _websockets.connection_manager import ConnectionManager  # Corrected import
from _websockets.message_handler import handle_message
import uuid
from utils.logging import logger

app = FastAPI()

# Initialize the connection manager
manager = ConnectionManager()

@app.websocket("")
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

if __name__ == "__main__":
    uvicorn.run(
            "main:app", 
            host="localhost", 
            port=8000, 
            reload=True,  # Enable auto-reload during development
            log_level="info"
        )