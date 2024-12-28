from typing import TypedDict, List, Dict

from schema import (
    WSMessage, 
    Result, 
    AgentResult, 
    ModelMessage
)
# from pymongo.server_api import ServerApi
# from config import MONGODB_URL
# from fastapi import WebSocket
# from pymongo import AsyncMongoClient

# print(MONGODB_URL)
# async_mongodb_client = AsyncMongoClient(MONGODB_URL)
# print(async_mongodb_client)

class State(TypedDict):
    ws_id: int
    final_result: Dict[str,  Result]
    chat_limit: int = 5
    chat_finished: bool = False
    chat_count: int = 0
    previous_node: str = ""
    next_node: str = ""
    previous_search_queries: List[str] = []
    ws_message: WSMessage
    agent_results: Dict[str, AgentResult] = {}
    requirements: dict = {}
    human_response: str = ""
    ai_response: str = ""
    session_id: str
    message_history: List[ModelMessage] = []
