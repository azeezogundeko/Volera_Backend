import asyncio
from typing import List, TypedDict

from utils.logging import logger
from fastapi import WebSocket


class MetadataWebsocket(TypedDict):
    url: str
    img_url: str
    title: str


async def send_sources(
    websocket: WebSocket, 
    metadata: List[MetadataWebsocket], 
) -> None:

    try:
        sources_payload = {
            "type": "sources",
            "data": [
                {
                    "metadata": source_metadata
                } for source_metadata in metadata
            ]
        }
        
        await websocket.send_json(sources_payload)
        logger.info(f"Sent {len(metadata)} sources via WebSocket")
    
    except Exception as e:
        logger.error(f"Failed to send sources: {str(e)}")
        raise


async def send_images(
    websocket: WebSocket, 
    images: List[MetadataWebsocket]
) -> None:
    try:
        sources_payload = {
            "type": "image_search",
            "data": images
        }
        
        await websocket.send_json(sources_payload)
    except Exception as e:
        logger.error(f"Failed to send sources: {str(e)}")
        raise

async def stream_final_response(
    websocket: WebSocket, 
    page_content: str
):
    """
    Stream the final response to the WebSocket client word by word.

    Args:
        websocket (WebSocket): Active WebSocket connection
        final_response (str): Complete response to stream
        delay (float): Delay between words to simulate natural typing
    """
    try:
        await websocket.send_json({"type": "message", "content": page_content})
        await websocket.send_json({"type": "messageEnd", "content": page_content})
    except Exception as e:
        logger.error(f"Error streaming final response: {e}", exc_info=True)
        await send_error_response(
            websocket, 
            "Error streaming response", 
            "STREAMING_ERROR"
        )
        


async def stream_ai_response(
    websocket: WebSocket, 
    final_response: str,
    delay: float = 0.05
):

    try:
        # Preprocess the response
        words = final_response.strip().split()
        
        # Stream response word by word
        for word in words:
            await websocket.send_json({
                "type": "message",
                "content": word + " "
            })
            await asyncio.sleep(delay)
        
        # Send final message marker
        await websocket.send_json({
            "type": "messageEnd",
            "content": final_response,
        })

    except Exception as e:
        logger.error(f"Error streaming final response: {e}", exc_info=True)
        await send_error_response(
            websocket, 
            "Error streaming response", 
            "STREAMING_ERROR"
        )
        
async def send_error_response(
    websocket: WebSocket, 
    message: str, 
    error_key: str
):
    """Send standardized error response to WebSocket client."""
    await websocket.send_json({
        "type": "error",
        "data": message,
        "key": error_key,
    })
