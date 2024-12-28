from typing import List

from agents import copilot_agent_graph
from db.sqlite.manager import session_manager
from _websockets.schema import WebSocketMessage, MessageData
from utils.websocket import WebSocketManager
# from .message_handler import handle_message

from utils.logging import logger
from fastapi import WebSocket


class ConnectionManager:
    def __init__(
        self 
    ):
        self.websocket_manager = WebSocketManager()
        self.active_connections: List[WebSocket] = []
        self.connection_count: int = 0


    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        logger.info(f"New connection established. Total active connections: {self.connection_count}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_count -= 1
            logger.info(f"Connection closed. Remaining active connections: {self.connection_count}")
    
    
    def start_session(self, user_id: str, ws_message: MessageData):
        metadata = {
            "focus_mode": ws_message.focus_mode,
            "optimization_mode": ws_message.optimization_mode,
            "title": self.generate_title_from_content(ws_message.content),
            "chat_id": ws_message.chat_id
        }

        session_id = session_manager.start_session(user_id, metadata)
        return session_id


    async def copilot_mode(self, user_id ,ws_message: MessageData, websocket: WebSocket) -> None:
        try:
            # result = await copilot_agent_graph()
            processing_config = {
                "configurable": {
                    "thread_id": user_id,
                }
            }
            session_id = self.start_session(user_id, ws_message)

            websocket_id = self.websocket_manager.add_connection(websocket)
            # Create initial state
            state = {
                "agent_results": {},
                "ws_message": ws_message.model_dump(),
                "human_response": ws_message.content,
                "ai_response": "",
                "session_id": session_id,
                "ws_id": websocket_id 
            }
            
            await copilot_agent_graph.ainvoke(
                state,
                processing_config,
            )
            session_manager.end_session(session_id, status='completed')
            self.websocket_manager.remove_connection(websocket_id)

        except Exception as e:
            self.websocket_manager.remove_connection(websocket_id)
            logger.error(f"Error in message handling: {e}", exc_info=True)
            session_manager.end_session(session_id, 'error')
            import traceback
            print(traceback.format_exc())
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        

    async def comprison_mode(self, websocket: WebSocket) -> None:
        ...

    async def handle_message(
        self, 
        data: WebSocketMessage, 
        websocket: WebSocket, 
        user_id: str
        ):
        print(data.data.focus_mode)
        if data.data.focus_mode == "copilot":
            ws_message = data.data
            await self.copilot_mode(user_id, ws_message, websocket)
        elif data.data.focus_mode == "comparison":
            await self.comprison_mode(websocket)
        


    def generate_title_from_content(self, content: str, max_length: int = 10) -> str:
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