from typing import TypedDict, List, Dict

from schema import (
    WSMessage, 
    Result, 
    AgentResult, 
    ModelMessage
)

from fastapi import WebSocket



class State(TypedDict):
    ws: WebSocket
    final_result: Dict[str,  Result]
    chat_limit: int = 5
    chat_finished: bool = False
    previous_node: str = ""
    previous_search_queries: List[str] = []
    ws_message: WSMessage
    agent_results: Dict[str, AgentResult] = {}
    requirements: dict = {}
    human_response: str = ""
    ai_response: str = ""
    session_id: str
    message_history: List[ModelMessage] = []
