from typing import Optional
import asyncio

from api.auth import services
from api.auth.schema import UserIn
from .schema import WebSocketMessage, RequestWebsockets
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


async def handle_request(raw_data: dict, websocket, user_id, history):
    request_type = raw_data.get("type")
    new_history = []
    
    if request_type in ["FILTER_REQUEST", "AGENT_REQUEST"]:
        data = RequestWebsockets(**raw_data)
        if request_type == "FILTER_REQUEST":
            new_history = await manager.filter_mode(data, websocket, user_id, history)
        else:  # AGENT_REQUEST
            new_history = await manager.agent_mode(data, websocket, user_id, history)

    elif request_type == "PRODUCT_DETAILS_REQUEST":
        new_history = await manager.detail_mode(raw_data, websocket, user_id, history)

    elif request_type == "COMPARE_REQUEST":
        new_history = await manager.compare_mode(raw_data, websocket, user_id, history)

    elif request_type == "message":
        print(raw_data)
        data = WebSocketMessage(**raw_data)
        await manager.handle_message(data, websocket, user_id)
    else:
        # Optionally handle unknown request types
        print(f"Unknown request type: {request_type}")

    return new_history



async def handle_websocket_messages(websocket: WebSocket, user_id):
    history = []
    
    while True:
        try:
            # Wait for a message with a 300 second timeout.
            raw_data = await asyncio.wait_for(websocket.receive_json(), timeout=500.0)
            if raw_data is None:
                continue
            new_history = await handle_request(raw_data, websocket, user_id, history)
               # Ensure new_history is iterable before concatenating.
            if new_history is None:
                new_history = []
            history += new_history

        except WebSocketDisconnect:
            await websocket.close()
            break

        except asyncio.TimeoutError:
            # Handle the timeout specifically.
            logger.error("WebSocket timeout occurred. Disconnecting websocket.")
            await websocket.close()
            break

        # except Exception as e:
        #     # Log any other exceptions and send an error message back.
        #     logger.error(f"Error processing message: {e}", exc_info=True)
        #     await manager.send_error(websocket)
        #     break

