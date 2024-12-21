import json
from pprint import pprint
from typing import Dict, Any
from fastapi import WebSocket

from schema import History, WSMessage, Message

from utils.logging import logger
from typing import Optional
from graph import agent_graph 

def parse_data(data: dict, user_id)-> WSMessage:
    message= Message(
        message_id=data["message"]["messageId"],
        chat_id=data["message"]["chatId"],
        content=data["message"]["content"],
        role="human"
    )
    histories = []
    for h in data["history"]:
        history = History(
            speaker=h["speaker"],
            message=h["message"],
            timestamp=h["timestamp"]
        )
        histories.append(history)
    ws_message = WSMessage(
        user_id= user_id,
        focus_mode="copilot",
        files=data["files"],
        optimization_mode=data["optimizationMode"],
        history=histories,
        message=message           
    )
    
    return ws_message

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
        parsed_state = parse_data(parsed_message, user_id)
    except json.JSONDecodeError:
        await _send_error_response(
            websocket, 
            "Invalid JSON format", 
            "JSON_DECODE_ERROR"
        )
        return

    # Stream agent graph processing
    processing_config = {
        "configurable": {
            "thread_id": user_id,
        }
    }
    try:
        # Use ainvoke to get the complete state
        state = await agent_graph.ainvoke(
            {"ws_message": [parsed_state]},
            processing_config,
        )
        
        # Extract final result safely
        final_result = state.get("final_result", "No response generated")
        
        # Prepare the response
        final_response = {
            "type": "message",
            "data": final_result
        }
        
        # Send the final response
        await websocket.send_json(data=final_response)
        
        # Send message end signal
        await websocket.send_json(
            data={
                "type": "messageEnd"
            }
        )
        
    except Exception as graph_error:
        logger.error(f"Agent graph processing error: {graph_error}", exc_info=True)
        await _send_error_response(
            websocket, 
            f"Error processing agent workflow: {str(graph_error)}", 
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