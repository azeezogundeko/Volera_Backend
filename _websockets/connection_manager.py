from typing import List, Dict, Any

from agents import (
    copilot_agent_graph,
    web_agent_graph, 
    insights_agent_graph,
    filter_agent,
    )
from _websockets.schema import WebSocketMessage, RequestWebsockets
# from api.product.services import filter_products
from db._appwrite.session import appwrite_session_manager
from utils.websocket import WebSocketManager
from api.chat.model import File
# from .message_handler import handle_message

from utils.logging import logger
from fastapi import WebSocket


class ConnectionManager:
    def __init__(
        self 
    ):
        self.websocket_manager = WebSocketManager()
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_count: int = 0

    def __config(self, ws_message, new_content, session_id, websocket_id, optimization_mode): 
        return {
            "agent_results": {},
            "ws_message": ws_message,
            "human_response": new_content,
            "ai_response": "",
            "optimization_mode": optimization_mode,
            "session_id": session_id,
            "ws_id": websocket_id,
            "chat_count": 0,
            "chat_finished": False,
            "chat_limit": 5,
            "ai_files": [],
            "message_data": None,
            }


    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        if user_id in self.active_connections:
            await self.disconnect(user_id)
        self.active_connections[user_id] = websocket
        await websocket.accept()
        self.connection_count += 1
        logger.info(
            f"New connection established for user {user_id}. Total active connections: {self.connection_count}")

    async def disconnect(self, user_id: str) -> None:
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.close()
            del self.active_connections[user_id]
            self.connection_count -= 1
            logger.info(
                f"Connection closed for user {user_id}. Remaining active connections: {self.connection_count}")
    
    
    async def start_session(self, user_id: str, data: WebSocketMessage):
        metadata = {
            "focus_mode": data.focus_mode,
            "optimization_mode": data.optimization_mode,
            "title": self.generate_title_from_content(data.data.content),
            "chat_id": data.data.chat_id,
            "file_ids": data.file_ids
        }
        session_id = await appwrite_session_manager.start_session(user_id, metadata)
        return session_id

    async def QA_mode(
        self, processing_config, state, websocket: WebSocket):
        try:  
            
            await web_agent_graph.ainvoke(
                state,
                processing_config,
            )
            self.websocket_manager.remove_connection(state["ws_id"])

        except Exception as e:
            self.websocket_manager.remove_connection(state["ws_id"])
            import traceback
            print(traceback.format_exc())
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })


    async def copilot_mode(
        self, processing_config , state, websocket: WebSocket) -> None:
        try:
  
            await copilot_agent_graph.ainvoke(
                state,
                processing_config,
            )
            self.websocket_manager.remove_connection(state["ws_id"])

        except Exception as e:
            self.websocket_manager.remove_connection(state["ws_id"])
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        

    async def insights_mode(self, processing_config, state, websocket: WebSocket) -> None:
        try:
            
            await insights_agent_graph.ainvoke(
                state,
                processing_config,
            )
            self.websocket_manager.remove_connection(state["ws_id"])

        except Exception as e:
            self.websocket_manager.remove_connection(state["ws_id"])
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        

    async def handle_message(
        self, 
        data: WebSocketMessage, 
        websocket: WebSocket, 
        user_id: str
        ):
        websocket_id = self.websocket_manager.add_connection(websocket)

        ws_message = data.data
        session_id = await self.start_session(user_id, data)

        new_content = await self.process_content(data.file_ids, session_id, ws_message.content)
        await appwrite_session_manager.log_message(ws_message.content, session_id, 'human')

        state = {
            "agent_results": {},
            "ws_message": ws_message.model_dump(),
            "human_response": new_content,
            "ai_response": "",
            "optimization_mode": data.optimization_mode,
            "session_id": session_id,
            "ws_id": websocket_id,
            "chat_count": 0,
            "chat_finished": False,
            "chat_limit": 5,
            "ai_files": [],
            "message_logs": [],
            }

        processing_config = {
                "configurable": {
                    "thread_id": user_id,
                }
            }

        if data.focus_mode == "copilot":
            await self.copilot_mode(processing_config, state, websocket)
        elif data.focus_mode == "insights":
            await self.insights_mode(processing_config, state, websocket)
        elif data.focus_mode == "all":
            await self.QA_mode(processing_config, state, websocket)


    async def filter_mode(self, data: RequestWebsockets, websocket: WebSocket, user_id:str) -> List[Dict[str, Any]]:
        websocket_id = self.websocket_manager.add_connection(websocket)
        results, ai_response = await filter_agent(data.data.message, data.data.currentProducts, data.data.currentFilters)

        await self.websocket_manager.send_json(
            websocket_id,
            {
            "type": "FILTER_RESPONSE",
            "filters": results,
            "aiResponse": ai_response
            }
        )

        

    async def process_content(self, file_ids: List[str], session_id: str, content: str):
        from utils.image import image_analysis, get_product_prompt, IMAGE_DESCRIPTION_PROMPT
        
        if not file_ids:
            return content
        c = content
        files = []
        # implement file processing using multimodal LLM to convert the text to a user message
        for file_id in file_ids:
            file = await File.get_file(file_id)
            files.append(file)

            # print(file)
            
        prompt = get_product_prompt(c, IMAGE_DESCRIPTION_PROMPT)
        try:
            text = await image_analysis(files, prompt)
            content = f""""
                    USER QUERY: {c}

                    IMAGE DESCRIPTIONS: {text}
                """ 
        except Exception as e:
            logger.error(f"Error processing image: {e}")

        
        

        return content


    def generate_title_from_content(self, content: str, max_length: int = 50) -> str:
        """
        Generate a concise title from the content
        
        Args:
            content (str): Full content text
            max_length (int): Maximum title length
        
        Returns:
            str: Summarized title
        """
        # Remove extra whitespaces
        content = ' '.join(content.split())
        
        # Strategy 1: Use first few words if content is short
        if len(content) <= max_length:
            return content[:max_length]
        
        # Strategy 2: Extract key phrases or first meaningful sentence
        sentences = content.split('.')
        
        # Remove very short or empty sentences
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        if sentences:
            # Use first sentence, truncated
            first_sentence = sentences[0]
            return first_sentence[:max_length] + ('...' if len(first_sentence) > max_length else '')
        
        # Fallback: truncate content
        return content[:max_length] + '...'



manager = ConnectionManager()