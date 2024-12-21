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
    # ws: WebSocket
    final_result: Dict[str,  Result]
    chat_limit: int = 5
    chat_finished: bool = False
    previous_node: str = ""
    previous_search_queries: List[str] = []
    ws_message: List[WSMessage]
    agent_results: Dict[str, AgentResult] = {}
    # message_history: List[ModelMessage]  
# {'type': 'message', 'message': {'messageId': '68370b35c14288', 'chatId': '089fb9cbf72af36d77bb6c8f7af8c0b873c01147', 'content': 'Best phone to buy in 2024'}, 'files': [], 'focusMode': 'webSearch', 'optimizationMode': 'speed', 'history': [{'speaker': 'human', 'message': 'Best phone to buy in 2024', 'timestamp': '2024-12-20T16:22:59.710Z'}]}