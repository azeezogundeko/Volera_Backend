import json

from graph import agent_graph 
from utils.logging import logger
from schema import History, WSMessage, Message
from db.sqlite.manager import session_manager
from db import push_sessions_to_appwrite

from fastapi import WebSocket

def parse_data(data: dict, user_id)-> WSMessage:
    message= Message(
        message_id=data["data"]["messageId"],
        content=data["data"]["content"],
        title=generate_title_from_content(data["data"]["content"]),
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
    try:
        # Parse and validate incoming message
        parsed_message = json.loads(message)
        parsed_state = parse_data(parsed_message, user_id)
    except json.JSONDecodeError:
        await websocket.send_json({
            "type": "error",
            "message": "Invalid JSON format"
        })
        return

    # Stream agent graph processing
    processing_config = {
        "configurable": {
            "thread_id": user_id,
        }
    }
    metadata = {
        "focus_mode": parsed_state["focus_mode"],
        "optimization_mode": parsed_state["optimization_mode"],
        "title": parsed_state["message"]["title"],
    }
    session_id = session_manager.start_session(user_id, metadata)
    session_manager.log_message(session_id, 'human', parsed_state["message"]["content"])
    try:
        await agent_graph.ainvoke(
            {
                "ws": websocket,
                "ws_message": parsed_state,
                "human_response": "",
                "ai_response": "",
                "session_id": session_id
            },
            processing_config,
        )
        session_manager.end_session(session_id, status='completed')
    except Exception as e:
        logger.error(f"Error in message handling: {e}", exc_info=True)
        session_manager.end_session(session_id, 'error')
        await push_sessions_to_appwrite()

        await websocket.send_json({
            "type": "error",
            "message": "Internal server error"
        })


def generate_title_from_content(content: str, max_length: int = 50) -> str:
    """
    Generate a concise title from the content
    
    Args:
        content (str): Full content text
        max_length (int): Maximum title length
    
    Returns:
        str: Summarized title
    """
    # Remove extra whitespaces
    content = ' '.join(content.split())
    
    # Strategy 1: Use first few words if content is short
    if len(content) <= max_length:
        return content[:max_length]
    
    # Strategy 2: Extract key phrases or first meaningful sentence
    sentences = content.split('.')
    
    # Remove very short or empty sentences
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    if sentences:
        # Use first sentence, truncated
        first_sentence = sentences[0]
        return first_sentence[:max_length] + ('...' if len(first_sentence) > max_length else '')
    
    # Fallback: truncate content
    return content[:max_length] + '...'
