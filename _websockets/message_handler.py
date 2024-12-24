import json

from graph import agent_graph 
from utils.logging import logger
from schema import History, WSMessage, Message

from fastapi import WebSocket

def parse_data(data: dict, user_id)-> WSMessage:
    print(data)
    message= Message(
        message_id=data["messageId"],
        chat_id=data["chatId"],
        content=data["content"],
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
        # await save_chat(state)
    except Exception as e:
        logger.error(f"Error in message handling: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "data": str(e)
        })

