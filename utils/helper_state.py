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

def flatten_history(history: List[str]) -> List[str]:
    history = [f"[{h.speaker}]: {h.message}" for h in history]
    if history:
        return history[-5]
    else:
        return [""]