from typing import List, TypedDict

from fastapi import WebSocket
from ..dataclass.state import Message 

class WebSocketSchema(TypedDict):
    ws: WebSocket
    chat_limit: int = 5
    ws_message: List[Message]
    chat_finished: bool = False
    final_result: dict | None = {}
    agent_results: dict | None = {}
    previous_node: str | None = None
    previous_search_queries: List[dict] | None = []
