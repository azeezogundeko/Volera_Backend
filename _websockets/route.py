from .connection_manager import manager

from fastapi import WebSocket, APIRouter
from utils.logging import logger
from .services import authenticate_user, extract_token, handle_websocket_messages


router = APIRouter()

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):

    try:
        # Extract and validate token before accepting connection
        token = await extract_token(websocket)
        if not token:
            return
            
        # Authenticate user before accepting connection
        user = await authenticate_user(websocket, token)
        if not user:
            return
            
        # Now that authentication is successful, accept connection
        await websocket.accept()
        logger.info(f"User authenticated and connected: {user.id}")
        
        # Handle messages
        await handle_websocket_messages(websocket, user.id)
        
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011)
        except:
            pass