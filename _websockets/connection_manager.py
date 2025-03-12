from appwrite.id import ID
from typing import List, Dict, Any

from agents import (
    copilot_agent_graph,
    web_agent_graph, 
    insights_agent_graph,
    ultra_search_agent_graph,
    filter_agent,
    response_agent,
    comparison_agent,
    product_agent,
    )
from agents.memory import mem_agent
from agents.tools.schema import extract_dataclass_messages

from _websockets.schema import WebSocketMessage, RequestWebsockets
# from api.product.services import filter_products
from db._appwrite.session import appwrite_session_manager
from utils.websocket import WebSocketManager
from utils.search_cache import search_cache_manager
from utils.memory import store
from api.chat.model import File
# from .message_handler import handle_message

from utils.logging import logger
from fastapi import WebSocket
from fastapi import WebSocketDisconnect


class ConnectionManager:
    def __init__(
        self 
    ):
        self.websocket_manager = WebSocketManager()
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_count: int = 0

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
        title = self.generate_title_from_content(data.data.content)
        metadata = {
            "focus_mode": data.focus_mode,
            "model": data.model,
            "title": title,
            "chat_id": data.data.chat_id,
            "file_ids": data.file_ids
        }
        search_cache_manager.add_search_query(title)
        session_id, focus_mode = await appwrite_session_manager.start_session(user_id, metadata)
        return session_id, focus_mode

    async def QA_mode(
        self, processing_config, state, websocket: WebSocket):
            
        return await web_agent_graph.ainvoke(
            state,
            processing_config,
        )

    async def copilot_mode(
        self, processing_config , state, websocket: WebSocket) -> None:
    

        return await copilot_agent_graph.ainvoke(
            state,
            processing_config,
        )        

    async def insights_mode(self, processing_config, state, websocket: WebSocket) -> None:
        return await insights_agent_graph.ainvoke(
            state,
            processing_config,
        )
                    

    async def ultra_search_mode(self, processing_config , state, websocket: WebSocket):
        return await ultra_search_agent_graph.ainvoke(
            state,
            processing_config,
        )
       
        
    async def handle_message(
        self, 
        data: WebSocketMessage, 
        websocket: WebSocket, 
        user_id: str
        ):
        websocket_id = self.websocket_manager.add_connection(websocket)

        ws_message = data.data
        session_id, focus_mode = await self.start_session(user_id, data)

        new_content = await self.process_content(data.file_ids, session_id, ws_message.content)
        await appwrite_session_manager.log_message(ws_message.content, session_id, 'human')

        state = {
            "agent_results": {},
            "ws_message": ws_message.model_dump(),
            # "focus_mode": focus_mode,
            "human_response": new_content,
            "ai_response": "",
            "session_id": session_id,
            "ws_id": websocket_id,
            "chat_count": 0,
            "chat_finished": False,
            "chat_limit": 5,
            "ai_files": [],
            "message_logs": [],
            "user_id": user_id,
            "namespace": (user_id, "memories"),
            "model": data.model,
            "max_depth": 3,
            "current_depth": 0
            }

        processing_config = {
                "configurable": {
                    "thread_id": user_id,
                }
            }

        try:
            if focus_mode == "copilot":
                final_state = await self.copilot_mode(processing_config, state, websocket)
            elif focus_mode == "insights":
                final_state = await self.insights_mode(processing_config, state, websocket)
            elif focus_mode == "all":
                final_state = await self.QA_mode(processing_config, state, websocket)
            elif focus_mode == "ultrasearch":
                final_state = await self.ultra_search_mode(processing_config, state, websocket)


            # update a new memory
            # user_prompt = extract_dataclass_messages(final_state['message_history'])
            mem_agent_response = await mem_agent.run(user_prompt=str(final_state['message_history']))
            result_data = mem_agent_response.data
            print(result_data)
            store.put((user_id, "memories"), ID.unique(), {"text": result_data.summary})

        except WebSocketDisconnect:
            logger.warning(f"WebSocket disconnected for user {user_id} during message handling.")

        except Exception as e:
            logger.error(e, exc_info=True)
            self.websocket_manager.remove_connection(state["ws_id"])
            await websocket.send_json({
                "type": "progress",
                "progress": {
                    "status": "error"
                },
                "message": "Internal server error"
            })


    async def filter_mode(self, data: RequestWebsockets, websocket: WebSocket, user_id:str, history) -> List[Dict[str, Any]]:
        websocket_id = self.websocket_manager.add_connection(websocket)
        return await filter_agent(
            websocket_id,
            data.data.message, user_id,
            data.data.currentProducts,
            data.data.currentFilters,
            history,
            )

        
    async def detail_mode(self, data: dict, websocket: WebSocket, user_id: str, history):
        websocket_id = self.websocket_manager.add_connection(websocket)
        data = data["data"]
        query = data["query"]
        product = data["product"]
        return await response_agent(websocket_id, user_id, query, product, history)

    async def agent_mode(self, data: RequestWebsockets, websocket: WebSocket, user_id: str, history):
        websocket_id = self.websocket_manager.add_connection(websocket)
        # data = data["data"]
        # query = data["message"]
        # product = data["product"]
        d = data.data
        return await product_agent(websocket_id, user_id, d.message, d.currentProducts, history)

    async def compare_mode(self, data: dict, websocket: WebSocket, user_id: str, message_history):
        websocket_id = self.websocket_manager.add_connection(websocket)
        data = data["data"]
        query = data["query"]
        products = data["products"]
        return await comparison_agent(websocket_id, user_id, query, products, message_history)

        

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

    async def send_error(self, websocket: WebSocket):
        await websocket.send_json({
        "type": "ERROR",
        "message": "Oops! Something went wrong on our end. Please try again later."
    })




manager = ConnectionManager()