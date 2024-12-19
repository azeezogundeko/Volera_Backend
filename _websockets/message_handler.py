import json
from typing import Dict, Any
from fastapi import WebSocket

from utils.logging import logger
from typing import Optional
from graph import agent_graph  

async def handle_message(message: str, websocket: WebSocket, user_id: str):
    """
    Handle incoming WebSocket messages with robust processing and error management.
    
    Args:
        message (str): Incoming WebSocket message
        websocket (WebSocket): Active WebSocket connection
        user_id (str): Unique identifier for the user session
    """
    try:
        # Parse and validate incoming message
        parsed_message = json.loads(message)
    except json.JSONDecodeError:
        await _send_error_response(
        websocket, 
        "Invalid JSON format", 
        "JSON_DECODE_ERROR"
    )
        
    # Validate message structure
    if not _validate_message_structure(parsed_message):
        await _send_error_response(
            websocket, 
            "Invalid message format", 
            "INVALID_FORMAT"
        )
        return

    # Prepare message for agent processing
    parsed_ws_message = _prepare_ws_message(parsed_message)
    
    logger.info(f"Processing message: {parsed_ws_message}")

    # Stream agent graph processing
    processing_config = {
        "configurable": {
            "thread_id": user_id,
        }
    }
    try:
        state = agent_graph.invoke(
            {
                "wsMessages": [parsed_ws_message],
                "ws": websocket,
            },
            processing_config
        )
        return await websocket.send_json(
                data ={
                    "type": "message",
                    "data": state["final_response"],
                }
        )
        
    except Exception as graph_error:
        logger.error(f"Agent graph processing error: {graph_error}", exc_info=True)
        await _send_error_response(
            websocket, 
            "Error processing agent workflow", 
            "AGENT_PROCESSING_ERROR"
        )



async def _send_error_response(
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

def _validate_message_structure(message: Dict[str, Any]) -> bool:
    """Validate incoming message structure."""
    return (
        "message" in message and 
        "content" in message["message"]
    )

def _prepare_ws_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare WebSocket message for agent processing."""
    ws_message = message.copy()
    ws_message["focusMode"] = ws_message.get(
        "focusMode", 
        "default_mode"
    )
    ws_message["history"] = ws_message.get("history", [])
    return ws_message

async def _stream_chunk_to_client(
    websocket: WebSocket, 
    chunk: Dict[str, Any]
):
    """Stream processing chunks to WebSocket client."""
    await websocket.send_text(chunk.get("message", "Processing"))

def _extract_final_response(chunks: list) -> str:
    """Extract final response from processing chunks."""
    final_chunk = chunks[-1] if chunks else {}
    return final_chunk.get("message", "No response generated")

async def _stream_final_response(
    websocket: WebSocket, 
    final_response: str, 
    message_id: Optional[str] = None
):
    """
    Stream the final response to the WebSocket client with chunked delivery.
    
    Args:
        websocket (WebSocket): Active WebSocket connection
        final_response (str): Complete response to stream
        message_id (Optional[str]): Optional message ID for tracking
    """
    try:
        # Define chunk size for streaming
        chunk_size = 50  # Adjust based on your preference
        
        # Stream response in chunks
        for i in range(0, len(final_response), chunk_size):
            chunk = final_response[i:i+chunk_size]
            await websocket.send_json({
                "type": "message_chunk",
                "data": chunk,
                "messageId": message_id,
                "is_final": i + chunk_size >= len(final_response)
            })
            await asyncio.sleep(0.05)  # Small delay to simulate natural typing
        
        # Send final message marker
        await websocket.send_json({
            "type": "message",
            "data": final_response,
            "messageId": message_id,
            "is_complete": True
        })

    except Exception as e:
        logger.error(f"Error streaming final response: {e}", exc_info=True)
        await _send_error_response(
            websocket, 
            "Error streaming response", 
            "STREAMING_ERROR"
        )