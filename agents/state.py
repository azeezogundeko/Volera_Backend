from typing import TypedDict, List, Dict, Optional

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

class MessageLog(TypedDict):
    type: str
    content: str 
    images: Optional[List[dict]]
    sources: Optional[List[dict]]
    products: Optional[List[dict]] 

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
    optimization_mode: str
    agent_results: Dict[str, AgentResult] = {}
    requirements: dict = {}
    human_response: str = ""
    ai_response: str = ""
    session_id: str
    ai_files: List[str] = []
    task_id: int
    images: List[dict] = []
    sources: List[dict] = []
    products: List[dict] = []
    message_history: List[ModelMessage] = []
    message_data: MessageLog = None
    user_id: str = ""
    model: str
    max_depth: int = 5
    current_depth: int = 0
    namespace: tuple = ()