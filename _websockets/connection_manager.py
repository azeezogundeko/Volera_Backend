import asyncio
import uuid
from fastapi import WebSocket
from typing import List, Optional
from urllib.parse import urlparse, parse_qs

from utils.logging import logger
from .message_handler import handle_message


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_count: int = 0

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection and add it to active connections.
        
        Args:
            websocket (WebSocket): The incoming WebSocket connection
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        logger.info(f"New connection established. Total active connections: {self.connection_count}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from active connections.
        
        Args:
            websocket (WebSocket): The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_count -= 1
            logger.info(f"Connection closed. Remaining active connections: {self.connection_count}")


    async def handle_connection(self, websocket: WebSocket, path: Optional[str]) -> None:
        """
        Handle a new WebSocket connection, including message processing.
        
        Args:
            websocket (WebSocket): The incoming WebSocket connection
            path (Optional[str]): The connection path with potential query parameters
        """
        user_id = str(uuid.uuid4())

        try:
            # Parse query parameters if path is provided
            query_params = {}
            if path:
                parsed_url = urlparse(path)
                query_params = parse_qs(parsed_url.query)

            logger.info(f"New connection: user_id={user_id}, query_params={query_params}")

            # Handle incoming messages
            async for message in websocket.iter_text():
                await handle_message(message, websocket, user_id)

        except Exception as e:
            logger.error(f"WebSocket connection error for user_id={user_id}", exc_info=True)
            try:
                await websocket.send_json({
                    "type": "error",
                    "data": "Internal server error.",
                    "key": "INTERNAL_SERVER_ERROR",
                })
            except Exception:
                pass
        finally:
            signal_task.cancel()  # Cancel signal task if active
            self.disconnect(websocket)
            logger.info(f"Connection closed for user_id={user_id}")
