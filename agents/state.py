from typing import TypedDict, Annotated, List, Dict, Any
from schema import (
    WSMessage, 
    Result, 
    AgentResult, 
    ModelMessage, 
    ModelRequest, 
    SystemPromptPart, 
    UserPromptPart
)

from langgraph.graph.message import add_messages
from fastapi import WebSocket

class State(TypedDict):
    # ws: WebSocket
    final_result: Dict[str,  Result]
    chat_limit: int
    chat_finished: bool
    previous_node: str
    previous_search_queries: Annotated[List[dict], add_messages]
    ws_message: Annotated[List[WSMessage], add_messages]
    agent_results: Dict[str, AgentResult]
    message_history: List[ModelMessage]  


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

def add_to_message_history(state: State, message: ModelMessage) -> None:
    if "message_history" not in state:
        state["message_history"] = []
    state["message_history"].append(message)

def get_message_history(state: State) -> List[ModelMessage]:
    return state.get("message_history", [])

def get_last_system_prompt(state: State) -> SystemPromptPart | None:
    history = get_message_history(state)
    for message in reversed(history):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, SystemPromptPart):
                    return part
    return None

def get_last_user_prompt(state: State) -> UserPromptPart | None:
    history = get_message_history(state)
    for message in reversed(history):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    return part
    return None

def truncate_message_history(state: State, max_length: int = 10) -> None:
    if "message_history" in state:
        state["message_history"] = state["message_history"][-max_length:]

def flatten_history(history: List[ModelMessage]) -> List[str]:
    history = [f"[{h.speaker}]: {h.message}" for h in history]
    if history:
        return history[:5]
    else:
        return [""]