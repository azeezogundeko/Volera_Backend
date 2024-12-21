from typing import Any, List
from schema import WSMessage
from agents.state import State

# Helper function to get a key's value from the state
def get_from_state(state: State, key: str, default: Any = None) -> Any:
    return state.get(key, default)

def get_current_request(state: State) -> WSMessage | None:
    messages = state.get("ws_message", [])
    return messages[-1] if messages else None

# Helper function to append a message to ws_message list
def append_ws_message(state: State, message: Any) -> None:
    if "ws_message" not in state:
        state["ws_message"] = []
    state["ws_message"].append(message)

# def add_to_message_history(state: State, message: ModelMessage) -> None:
#     if "message_history" not in state:
#         state["message_history"] = []
#     state["message_history"].append(message)




# def get_last_user_prompt(state: State) -> UserPromptPart | None:
#     history = get_message_history(state)
#     for message in reversed(history):
#         if isinstance(message, ModelRequest):
#             for part in message.parts:
#                 if isinstance(part, UserPromptPart):
#                     return part
#     return None

def truncate_message_history(state: State, max_length: int = 10) -> None:
    if "message_history" in state:
        state["message_history"] = state["message_history"][-max_length:]

def flatten_history(history: List[dict]) -> List[str]:
    """
    Flatten the history list into a list of formatted history strings.
    
    Args:
        history (List[dict]): List of history dictionaries with 'speaker' and 'message' keys
    
    Returns:
        List[str]: List of formatted history strings, limited to the last 5 entries
    """
    try:
        # Print raw history for debugging
        print("Raw history:", history)
        
        # Safely format history entries
        formatted_history = []
        for h in history:
            # Ensure the history item is a dictionary and has required keys
            if isinstance(h, dict) and 'speaker' in h and 'message' in h:
                formatted_entry = f"[{h['speaker']}]: {h['message']}"
                formatted_history.append(formatted_entry)
        
        # Return last 5 entries or all if less than 5
        return formatted_history[-5:] if formatted_history else [""]
    
    except Exception as e:
        # Log any unexpected errors
        print(f"Error in flatten_history: {e}")
        return [""]