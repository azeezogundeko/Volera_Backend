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
        message_id=data["data"]["messageId"],
        chat_id=data["data"]["chatId"],
        content=data["data"]["content"],
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
        files=data["fileIds"],
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
        state = await agent_graph.ainvoke(
            {
                "ws": websocket,
                "ws_message": parsed_state,
                "human_response": "",
                "ai_response": "",
            },
            processing_config,
        )
        #     print(chunk)
        #     # Handle interrupts
        #     if "copilot" in chunk:
        #         await websocket.send_json({
        #             "type": "message",
        #             "content": chunk["copilot"]["ai_response"]
        #         })
        #         await websocket.send_json({
        #             "type": "messageEnd",
        #         })
        #         print("====================================")
        #         # Wait for user input
        #         response = await websocket.receive_text()
        #         # Update state with user response
        #         print(response)
        #         chunk["human_response"] = response["data"]["content"]

        #     # Track the final state
        #     if chunk:
        #         state = chunk

        # # Ensure state is not None
        if state is None:
            raise ValueError("No valid state generated")

        # Extract final result safely
        final_result = state.get("final_result", {
            "content": "No response generated",
            "sources": []
        })

        # Send sources if available
        if final_result.get("sources"):
            await websocket.send_json({
                "type": "sources",
                "data": final_result["sources"]
            })

        _stream_final_response(
            websocket,
            final_result.get("content", "No response generated"))
    except Exception as e:
        logger.error(f"Error in message handling: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "data": str(e)
        })


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


async def _stream_final_response(
    websocket: WebSocket, 
    final_response: str
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
                "type": "message",
                "content": chunk
            })
            await asyncio.sleep(0.05)  # Small delay to simulate natural typing
        
        # Send final message marker
        await websocket.send_json({
            "type": "messageEnd",
            "content": final_response,
        })

    except Exception as e:
        logger.error(f"Error streaming final response: {e}", exc_info=True)
        await _send_error_response(
            websocket, 
            "Error streaming response", 
            "STREAMING_ERROR"
        )