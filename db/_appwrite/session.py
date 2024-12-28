# import json
# import uuid
# from typing import Dict, Any, Literal, Optional
# from datetime import datetime, timedelta, timezone

# from schema.dataclass.database import Message, Chat, File

# from .base import async_appwrite
# from .chat import create_chat, create_message
# from utils.logging import logger

# class AppwriteSessionManager:
#     def __init__(self):
#         """
#         Initialize session management using existing async Appwrite client
#         """
#         self.sessions_collection_id = 'user_sessions'
#         self.message_collection_id = "messages"
#         self.chat_collection_id = "chats"

#     async def start_session(
#         self, 
#         user_id: str, 
#         metadata: Optional[Dict[str, Any]] = None, 
#         duration: int = 3600
#     ) -> Dict[str, Any]:
#         """
#         Create a new user session in Appwrite
        
#         :param user_id: Unique identifier for the user
#         :param metadata: Additional session metadata
#         :param duration: Session duration in seconds
#         :return: Session details
#         """
#         try:
#             session_id = async_appwrite.get_unique_id()
#             title = metadata.get("title")
#             focus_mode = metadata.get("focus_mode")
#             files = metadata.get("files")
#             title = metadata.get("title")

#             start_time = datetime.now(timezone.utc)
#             end_time = start_time + timedelta(seconds=duration)
#             fs = []
#             if files:
#                 for file in files:
#                     fs.append(File(
#                         name=file["name"],
#                         field_id=async_appwrite.get_unique_id(),
#                     ))
#             chat_payload = Chat(
#                 title=title,
#                 user_id=user_id,
#                 start_time=start_time,
#                 end_time=end_time,
#                 focus_mode=focus_mode,
#                 files=fs
#             )
#             await async_appwrite.create_document(
#                 self.chat_collection_id,
#                 chat_payload.to_dict(),
#                 session_id      
#             )
#             # await create_message(chat_payload)
#             logger.info(f"Created session for user {user_id}: {session_id}")
#             return session_id

#         except Exception as e:
#             logger.error(f"Failed to create session: {str(e)}")
#             raise

#     async def log_message(
#         self, 
#         session_id: str, 
#         content: Any,
#         message_type: Literal["human", "assistant"], 
#         ):
        
#         message_payload = Message(
#             content=content,
#             chat_id=session_id,
#             role=message_type,
#             metadata=str(
#                 {

#                 }
#             )
#         )

#         await async_appwrite.create_document(
#         self.message_collection_id,
#         message_payload.to_dict(),
#         async_appwrite.get_unique_id()
#     )
   
#     async def end_session(self, session_id: str):
#         """
#         Explicitly end a session
        
#         :param session_id: Session identifier to end
#         """
#         try:
#             await async_appwrite.create_document(
#                 collection_id=self.sessions_collection_id,
#                 document_data={'status': 'ended'},
#                 document_id=session_id
#             )
#             logger.info(f"Ended session: {session_id}")
#         except Exception as e:
#             logger.error(f"Failed to end session: {str(e)}")


#     async def cleanup_expired_sessions(self):
#         """
#         Remove or mark expired sessions as inactive
#         """
#         try:
#             now = datetime.now(timezone.utc).isoformat()
            
#             # Find and update expired sessions
#             results = await async_appwrite.list_documents(
#                 collection_id=self.sessions_collection_id,
#                 queries=[
#                     "status = 'active'",
#                     f"end_time < '{now}'"
#                 ]
#             )

#             for session in results['documents']:
#                 await self.end_session(session['$id'])

#             logger.info(f"Cleaned up {results['total']} expired sessions")

#         except Exception as e:
#             logger.error(f"Session cleanup failed: {str(e)}")

# # Singleton instance for easy import and use
# appwrite_session_manager = AppwriteSessionManager()