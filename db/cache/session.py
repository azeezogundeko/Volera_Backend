import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Literal

import redis.asyncio as redis

from utils.logging import logger
from .._appwrite.chat import create_chat, create_message
from schema.dataclass.database import Chat, Message

class RedisSessionManager:
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        """
        Initialize Redis session manager
        
        :param redis_url: Redis connection URL
        """
        self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        
        # Key prefixes for different types of data
        self.SESSION_PREFIX = "session:"
        self.MESSAGE_PREFIX = "message:"
        self.USER_SESSIONS_PREFIX = "user_sessions:"

    async def start_session(
        self, 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None, 
        duration: int = 3600
    ) -> str:
        """
        Create a new user session in Redis
        
        :param user_id: Unique identifier for the user
        :param metadata: Additional session metadata
        :param duration: Session duration in seconds
        :return: Session ID
        """
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Prepare session metadata
            start_time = datetime.now(timezone.utc)
            end_time = start_time + timedelta(seconds=duration)
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'status': 'active',
                'metadata': json.dumps(metadata or {})
            }
            
            # Store session data
            await self.redis.hmset(f"{self.SESSION_PREFIX}{session_id}", session_data)
            
            # Set expiration for the session
            await self.redis.expire(f"{self.SESSION_PREFIX}{session_id}", duration)
            
            # Track user's active sessions
            await self.redis.sadd(f"{self.USER_SESSIONS_PREFIX}{user_id}", session_id)
            
            logger.info(f"Created Redis session for user {user_id}: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create Redis session: {str(e)}")
            raise

    async def log_message(
        self, 
        session_id: str, 
        content: str,
        message_type: Literal["human", "assistant"],
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a message to a specific session
        
        :param session_id: Session identifier
        :param content: Message content
        :param message_type: Type of message (human or assistant)
        :param additional_metadata: Optional additional metadata
        :return: Message ID
        """
        try:
            message_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()
            
            message_data = {
                'message_id': message_id,
                'session_id': session_id,
                'content': content,
                'type': message_type,
                'timestamp': timestamp,
                'metadata': json.dumps(additional_metadata or {})
            }
            
            # Store message in Redis hash
            await self.redis.hset(f"{self.MESSAGE_PREFIX}{message_id}", message_data)
            
            # Add message to session's message list
            await self.redis.rpush(f"{self.SESSION_PREFIX}{session_id}:messages", message_id)
            
            logger.info(f"Logged message {message_id} to session {session_id}")
            return message_id

        except Exception as e:
            logger.error(f"Failed to log message: {str(e)}")
            raise

    async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all messages for a specific session
        
        :param session_id: Session identifier
        :return: List of message details
        """
        try:
            # Get list of message IDs for the session
            message_ids = await self.redis.lrange(f"{self.SESSION_PREFIX}{session_id}:messages", 0, -1)
            
            messages = []
            for msg_id in message_ids:
                message = await self.redis.hgetall(f"{self.MESSAGE_PREFIX}{msg_id}")
                messages.append(message)
            
            return messages

        except Exception as e:
            logger.error(f"Failed to retrieve session messages: {str(e)}")
            return []

    async def end_session(self, session_id: str):
        """
        End a specific session by creating a single chat with all messages
        
        :param session_id: Session identifier to end
        """
        try:
            # Retrieve all messages for the session
            messages = await self.get_session_messages(session_id)
            
            if not messages:
                logger.warning(f"No messages found for session {session_id}")
                return

            # Get session metadata
            session_data = await self.redis.hgetall(f"{self.SESSION_PREFIX}{session_id}")
            # Determine user ID and other metadata
            user_id = session_data.get('user_id', 'unknown')
            start_time = datetime.fromisoformat(session_data.get('start_time', datetime.now(timezone.utc).isoformat()))
            end_time = datetime.fromisoformat(session_data.get('end_time', datetime.now(timezone.utc).isoformat()))
            
            # Create a single chat for the entire session
            chat_payload = Chat(
                title=session_data.get('title', f"Session {session_id}"),
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                focus_mode=session_data.get('focus_mode', 'default'),
                files=[]
            )

            # Create the chat in Appwrite
            chat_result = await create_chat(chat_payload)
            chat_id = chat_result['$id']  # Assuming the result contains the chat ID

            # Prepare and create messages for this chat
            for message_data in messages:
                message_payload = Message(
                    content=message_data.get('content', ''),
                    chat_id=chat_id,
                    role=message_data.get('type', 'assistant'),
                    metadata=json.dumps({
                        'timestamp': message_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                        'original_message_id': message_data.get('message_id', '')
                    })
                )
                await create_message(message_payload)

            # Clean up Redis data
            user_id = session_data.get('user_id')
            if user_id:
                await self.redis.srem(f"{self.USER_SESSIONS_PREFIX}{user_id}", session_id)
            
            # Delete session and its messages from Redis
            await self.redis.delete(f"{self.SESSION_PREFIX}{session_id}")
            await self.redis.delete(f"{self.SESSION_PREFIX}{session_id}:messages")
            
            # Delete all associated message entries
            message_ids = await self.redis.lrange(f"{self.SESSION_PREFIX}{session_id}:messages", 0, -1)
            for msg_id in message_ids:
                await self.redis.delete(f"{self.MESSAGE_PREFIX}{msg_id}")
            
            logger.info(f"Ended and synced session: {session_id}")

        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {str(e)}")
            raise

# Singleton instance for easy import and use
redis_session_manager = RedisSessionManager()