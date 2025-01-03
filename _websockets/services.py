from typing import Optional

from api.auth import services
from api.auth.schema import UserIn
from .schema import WebSocketMessage
from .connection_manager import manager

from fastapi import WebSocket, WebSocketDisconnect
from utils.logging import logger
from jose import JWTError


async def extract_token(websocket: WebSocket) -> Optional[str]:
    """Extract and process the token from WebSocket query parameters."""
    token = websocket.query_params.get("token")
    logger.info(f"Received token: {token}")
    
    if not token:
        logger.error("No token provided")
        await websocket.close(code=4001, reason="Authentication required")
        return None
        
    if token.lower().startswith("bearer "):
        token = token.split(" ")[1]
        logger.info("Bearer token processed")
    
    return token


async def authenticate_user(websocket: WebSocket, token: str) -> Optional[UserIn]:
    """Authenticate user using the provided token."""
    try:
        logger.info("Verifying token")
        payload = services.decode_access_token(token)
        email = payload.get("sub")
        
        if not email:
            logger.error("Invalid token: no email in payload")
            await websocket.close(code=4001, reason="Invalid authentication token")
            return None
            
        logger.info(f"Token verified for email: {email}")
        user = await services.get_user(email)
        
        if not user:
            logger.error(f"User not found for email: {email}")
            await websocket.close(code=4001, reason="User not found")
            return None
            
        return user
        
    except JWTError as e:
        logger.error(f"JWT verification failed: {str(e)}")
        await websocket.close(code=4001, reason="Invalid authentication token")
        return None


async def handle_websocket_messages(websocket: WebSocket, user_id: str):
    """Handle incoming WebSocket messages."""
    try:
        while True:
            raw_data = await websocket.receive_json()
            data = WebSocketMessage(**raw_data)
            await manager.handle_message(data, websocket, user_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_id}")
        manager.disconnect(websocket)
