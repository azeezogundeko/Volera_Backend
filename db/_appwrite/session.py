
from typing import Dict, Any, Literal, Optional
from datetime import datetime, timezone

from schema.dataclass.database import Message, File

from .base import async_appwrite
from utils.logging import logger

class AppwriteSessionManager:
    def __init__(self):
        """
        Initialize session management using existing async Appwrite client
        """
        self.sessions_collection_id = 'user_sessions'
        self.message_collection_id = "messages"
        self.chat_collection_id = "chats"

    async def start_session(
        self, 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new user session in Appwrite
        
        :param user_id: Unique identifier for the user
        :param metadata: Additional session metadata
        :param duration: Session duration in seconds
        :return: Session details
        """
        try:
            session_id = metadata["chat_id"]
            focus_mode = metadata.get("focus_mode")
            files = metadata.get("files")
            title = metadata.get("title")

            fs = []
            if files:
                for file in files:
                    fs.append(File(
                        name=file["name"],
                        field_id=async_appwrite.get_unique_id(),
                    ))
            payload = {
                "title": title,
                "focus_mode": focus_mode,
                "files": fs,
            }
            await async_appwrite.update_document(
                self.chat_collection_id,
                document_data=payload,
                document_id=session_id
            )
            # await create_message(chat_payload)
            logger.info(f"Created session for user {user_id}: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise

    async def log_message(
        self, 
        session_id: str, 
        content: Any,
        message_type: Literal["human", "assistant"], 
        ):
        message_id = async_appwrite.get_unique_id() 
        message_payload = Message(
            content=content,
            chat_id=session_id,
            role=message_type,
            metadata=str(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        )

        await async_appwrite.create_document(
        self.message_collection_id,
        message_payload.to_dict(),
        message_id
    )

# Singleton instance for easy import and use
appwrite_session_manager = AppwriteSessionManager()