from typing import TypedDict, Annotated, List, Dict, Any
from schema import (
    WSMessage, 
    Result, 
    AgentResult, 
    ModelMessage
)

from langgraph.graph.message import add_messages
from fastapi import WebSocket

class State(TypedDict):
    ws: WebSocket
    final_result: Dict[str,  Result]
    chat_limit: int
    chat_finished: bool
    previous_node: str
    previous_search_queries: Annotated[List[dict], add_messages]
    ws_message: Annotated[List[WSMessage], add_messages]
    agent_results: Dict[str, AgentResult]
    message_history: List[ModelMessage]  
