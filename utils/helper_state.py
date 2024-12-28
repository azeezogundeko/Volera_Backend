import asyncio
from typing import Any, List, Dict

from schema import (
    History,
    ModelMessage, 
    ModelRequest, 
    ModelResponse, 
    UserPromptPart, 
    TextPart,
    SystemPromptPart
)
from .logging import logger
from schema import WSMessage
from fastapi import WebSocket
from agents.state import State



# Helper function to get a key's value from the state
def get_from_state(state: State, key: str, default: Any = None) -> Any:
    return state.get(key, default)

def get_current_request(state: State) -> WSMessage | None:
    messages = state.get("ws_message", {})
    return messages if messages else None

# Helper function to append a message to ws_message list
def append_ws_message(state: State, message: Any) -> None:
    if "ws_message" not in state:
        state["ws_message"] = []
    state["ws_message"].append(message)


def truncate_message_history(state: State, max_length: int = 10) -> None:
    if "message_history" in state:
        state["message_history"] = state["message_history"][-max_length:]

def flatten_history(history: List[dict], n_k=30) -> List[ModelMessage]:
    try:
        formatted_history = []
        for h in history:
            # Ensure the history item is a dictionary and has required keys
            if isinstance(h, dict) and 'speaker' in h and 'message' in h:
                formatted_entry = {
                    'speaker': h['speaker'], 
                    'message': h['message']
                }
                formatted_history.append(formatted_entry)
        
        # Return last n_k entries or all if less than n_k
        history_subset = formatted_history[-n_k:] if formatted_history else []
        return convert_history_to_model_messages(history_subset)
    
    except Exception as e:
        # Log any unexpected errors
        print(f"Error in flatten_history: {e}")
        return []

def update_history(state: State, user_message: str, ai_message: str) -> None:
   user_history =  History(
        speaker="human", 
        message=user_message
   )
   state["ws_message"]["history"].append(user_history)
   ai_history =  History(
        speaker="assistant", 
        message=ai_message
   )
   state["ws_message"]["history"].append(ai_history)

def get_user_ai_history(state: State) -> List[str]:
    # Update state with user response
    history = state["ws_message"]["history"]
    print(history)
    
    # Filter and get the last user and AI messages
    user_last_msg = next((msg for msg in reversed(history) if msg['role'] == 'human'), None)
    ai_last_msg = next((msg for msg in reversed(history) if msg['role'] == 'assistant'), None)
    
    # Validate and use the messages
    user_input = user_last_msg['message'] if user_last_msg else ""
    ai_response = ai_last_msg['message'] if ai_last_msg else ""
    
    return user_input, ai_response
   
async def stream_final_response(
    websocket: WebSocket, 
    final_response: str,
    delay: float = 0.1
):
    """
    Stream the final response to the WebSocket client word by word.

    Args:
        websocket (WebSocket): Active WebSocket connection
        final_response (str): Complete response to stream
        delay (float): Delay between words to simulate natural typing
    """
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



def convert_history_to_model_messages(history: List[Dict[str, str]]) -> List[ModelMessage]:
    model_messages = []
    for entry in history:
        speaker = entry.get('speaker', '')
        message = entry.get('message', '')
        
        if speaker == 'system':
            # Convert system message to ModelRequest with SystemPromptPart
            model_messages.append(ModelRequest(
                parts=[SystemPromptPart(content=message)]
            ))
        elif speaker == 'user':
            # Convert user message to ModelRequest with UserPromptPart
            model_messages.append(ModelRequest(
                parts=[UserPromptPart(content=message)]
            ))
        elif speaker == 'assistant':
            # Convert AI message to ModelResponse with TextPart
            model_messages.append(ModelResponse(
                parts=[TextPart(content=message)]
            ))
    
    return model_messages