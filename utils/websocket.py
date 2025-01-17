import json
import asyncio
from typing import List, TypedDict, Dict, Optional

from fastapi import WebSocket
from utils.logging import logger

class ProductSchema(TypedDict):
    product_id: str
    category: str
    name: str
    brand: str
    current_price: float
    old_price: Optional[float]
    discount: Optional[float]
    rating: Optional[float]
    rating_count: Optional[int]
    image: str
    url: str
    source: str
    relevance_score: float

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
        if status == "searching":
            data = {
                "type": "progress",
                "progress": {
                    "status": status,
                    "searched": searched_items
                }
            }
            return await self.get_websocket(ws_id).send_json(data)
        elif status == "scraping":
            data = {
                "type": "progress",
                "progress": {
                    "status": status,
                    "scraped": searched_items
                }
            }
            return await self.get_websocket(ws_id).send_json(data)


    async def send_search_complete(
        self, ws_id, total_searched: int, total_scraped: int
        ) ->WebSocket:
        data = {
            "type": "search_complete",
            "data": {
                "total_searched": total_searched,
                "total_scraped": total_scraped
            }
        }
        return await self.get_websocket(ws_id).send_json(data)

    async def send_product(self, ws_id: int, message_id, chat_id, product_data: List[dict]) -> None:
        # datas = [ProductSchema(**data) for data in product_data]
        
        await self.send_json(
            ws_id,
            {
                "type": "product",
                "messageId": message_id,
                "chatId": chat_id,
                "role": "assistant",
                "products": product_data
                # "content": 
            }
        )


    async def send_json(self, ws_id: int, data: dict) -> None:
        return await self.get_websocket(ws_id).send_json(data)

    async def receive_json(self, ws_id: int) -> str:
        """Receive a JSON message from a specific WebSocket connection with timeout"""
        websocket = self.get_websocket(ws_id)
        if not websocket:
            logger.error(f"WebSocket {ws_id} not found")
            return ""
        
        try:
            # Set a timeout for receiving messages
            data = await asyncio.wait_for(websocket.receive_json(), timeout=300.0)
            
            # Handle dictionary response
            if isinstance(data, dict):
                # Handle nested data structure
                if 'data' in data:
                    nested_data = data['data']
                    if isinstance(nested_data, dict):
                        return nested_data.get('content', '')
                    return str(nested_data)
                # Handle direct content
                if 'content' in data:
                    return data['content']
                # Handle message field
                if 'message' in data:
                    return data['message']
                # Return stringified dict if no known fields found
                return json.dumps(data)
            
            # Handle non-dict response
            return str(data)
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for WebSocket {ws_id} response")
            return ""
        except Exception as e:
            logger.error(f"Error receiving JSON from WebSocket {ws_id}: {e}", exc_info=True)
            return ""

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
