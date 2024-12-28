import asyncio
from typing import List, TypedDict, Dict, Optional
from fastapi import WebSocket
from utils.logging import logger

class ImageMetadata(TypedDict):
    url: str
    img_url: str
    title: str

class SourceMetadata(TypedDict):
    url: str
    content: str
    title: str

class WebSocketManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebSocketManager, cls).__new__(cls)
            cls._instance.websocket_map: Dict[int, WebSocket] = {}
        return cls._instance

    def add_connection(self, websocket: WebSocket) -> int:
        """Add a new WebSocket connection and return its ID"""
        ws_id = id(websocket)
        self.websocket_map[ws_id] = websocket
        return ws_id

    def remove_connection(self, ws_id: int) -> None:
        """Remove a WebSocket connection"""
        if ws_id in self.websocket_map:
            del self.websocket_map[ws_id]

    def get_websocket(self, ws_id: int) -> Optional[WebSocket]:
        """Get WebSocket instance by ID"""
        return self.websocket_map.get(ws_id)

    async def send_sources(self, ws_id: int, metadata: List[SourceMetadata]) -> None:
        """Send sources to a specific WebSocket connection"""
        websocket = self.get_websocket(ws_id)
        if not websocket:
            logger.error(f"WebSocket {ws_id} not found")
            return

        try:
            sources_payload = {
                "type": "sources",
                "sources": [
                    {
                        "pageContent": source["content"],
                        "metadata": {
                            "url": source["url"],
                            "title": source["title"]
                        }
                    }
                    for source in metadata
                ]
            }
            await websocket.send_json(sources_payload)
            logger.info(f"Sent {len(metadata)} sources via WebSocket {ws_id}")
        except Exception as e:
            logger.error(f"Failed to send sources: {str(e)}")
            raise

    async def send_progress(
        self, 
        ws_id: int, 
        status: str, 
        searched_items: int
        ) -> WebSocket:
        data = {
            "type": "progress",
            "progress": {
                "status": status,
                "searched": searched_items
            }
        }
        return await self.get_websocket(ws_id).send_json(data)


    async def send_search_complete(
        self, total_searched: int, total_scraped: int
        ) ->WebSocket:
        data = {
            "type": "search_complete",
            "data": {
                "total_searched": total_searched,
                "total_scraped": total_scraped
            }
        }
        return await self.get_websocket(ws_id).send_json(data)


    async def send_json(self, ws_id: int, data: dict) -> None:
        return await self.get_websocket(ws_id).send_json(data)

    async def receive_json(self, ws_id: int) -> dict:
        return await self.get_websocket(ws_id).receive_json()


    async def send_images(self, ws_id: int, images: List[ImageMetadata]) -> None:
        websocket = self.get_websocket(ws_id)
        if not websocket:
            logger.error(f"WebSocket {ws_id} not found")
            return

        try:
            sources_payload = {
                "type": "image_search",
                "data": images
            }
            await websocket.send_json(sources_payload)
        except Exception as e:
            logger.error(f"Failed to send images: {str(e)}")
            raise

    async def stream_final_response(self, ws_id: int, page_content: str) -> None:
        websocket = self.get_websocket(ws_id)
        if not websocket:
            logger.error(f"WebSocket {ws_id} not found")
            return

        try:
            await websocket.send_json({"type": "message", "content": page_content})
            await websocket.send_json({"type": "messageEnd", "content": page_content})
        except Exception as e:
            logger.error(f"Error streaming final response: {e}", exc_info=True)
            await self.send_error_response(ws_id, "Error streaming response", "STREAMING_ERROR")

    async def stream_ai_response(self, ws_id: int, final_response: str, delay: float = 0.05) -> None:
        """Stream AI response word by word to a specific WebSocket connection"""
        websocket = self.get_websocket(ws_id)
        if not websocket:
            logger.error(f"WebSocket {ws_id} not found")
            return

        try:
            words = final_response.strip().split()
            for word in words:
                await websocket.send_json({
                    "type": "message",
                    "content": word + " "
                })
                await asyncio.sleep(delay)

            await websocket.send_json({
                "type": "messageEnd",
                "content": final_response,
            })
        except Exception as e:
            logger.error(f"Error streaming AI response: {e}", exc_info=True)
            await self.send_error_response(ws_id, "Error streaming response", "STREAMING_ERROR")

    async def send_error_response(self, ws_id: int, message: str, error_key: str) -> None:
        """Send error response to a specific WebSocket connection"""
        websocket = self.get_websocket(ws_id)
        if not websocket:
            logger.error(f"WebSocket {ws_id} not found")
            return

        try:
            await websocket.send_json({
                "type": "error",
                "data": message,
                "key": error_key,
            })
        except Exception as e:
            logger.error(f"Failed to send error response: {str(e)}")

# Create a global instance of WebSocketManager
websocket_manager = WebSocketManager()
