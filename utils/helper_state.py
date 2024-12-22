from typing import Any, List
from schema import WSMessage
from agents.state import State
from schema import History

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
    try:
        formatted_history = []
        for h in history:
            # Ensure the history item is a dictionary and has required keys
            if isinstance(h, dict) and 'speaker' in h and 'message' in h:
                formatted_entry = f"[{h['speaker']}]: {h['message']}"
                formatted_history.append(formatted_entry)
        
        # Return last 5 entries or all if less than 5
        return formatted_history if formatted_history else [""]
    
    except Exception as e:
        # Log any unexpected errors
        print(f"Error in flatten_history: {e}")
        return [""]

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
   