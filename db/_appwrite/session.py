
from typing import Dict, Any, Literal, Optional, List
from datetime import datetime, timezone

from api.chat.model import Message, File, Chat


from .base import async_appwrite
from utils.logging import logger

from pydantic import BaseModel


class FileMessage(BaseModel):
    fileData: bytes
    fileName: str
    fileExtension: str

class AppwriteSessionManager:
    # def __init__(self):
    #     """
    #     Initialize session management using existing async Appwrite client
    #     """
    async def _process_files(self, files: List[FileMessage], session_id: str):
        for file in files:
            # f = InputFile.from_bytes(
            #     file.fileData,
            #     filename=file.fileName
            # )
            # file_id = File.get_unique_id()
            # await File.create_file(file_id, f)

            await File.create(
                document_id=file_id,
                data = {
                    "name": file.fileName,
                    "file_extension": file.fileExtension,
                    "chat_id": session_id
                    }
                )

                    # fs.append(
                    #     FileDT(
                    #         name=file["name"],
                    #         file_extension=file["file_extension"],
                    #         file_id=file_id
                    # ))


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
            file_ids = metadata.get("file_ids")
            title = metadata.get("title")

            # fs = []
            # if files:
            #     await self._process_files(files, session_id)
                

            payload = {
                "title": title,
                "focus_mode": focus_mode,
                "file_ids": file_ids,
            }
            await Chat.update(session_id, payload)
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
        file_ids: Optional[List[str]] = []
        ):

        # if files:
        #     await self._process_files(files, session_id)

        message_id = async_appwrite.get_unique_id() 
        message_payload = dict(
            content=content,
            chat_id=session_id,
            role=message_type,
            images=file_ids,
            metadata=str(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        )
        await Message.create(message_id, message_payload)




# Singleton instance for easy import and use
appwrite_session_manager = AppwriteSessionManager()