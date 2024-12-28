import sqlite3
import json

from config import CHAT_COLLECTION_ID, MESSAGE_COLLECTION_ID
from .._appwrite.chat import create_chat, create_message, async_appwrite

from schema.dataclass.database import Chat, Message
from utils.logging import logger



async def push_sessions_to_appwrite(db_path: str = 'sessions.db'):
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Retrieve incomplete or recent sessions
        cursor.execute('''
            SELECT session_id, user_id, start_time, end_time, status, metadata 
            FROM sessions 
            WHERE status != 'synced'
        ''')
        sessions = cursor.fetchall()

        for session in sessions:
            session_id, user_id, start_time, end_time, status, metadata = session
            
            try:
                # iso_start_time = convert_to_iso_format(start_time)
                # iso_end_time = convert_to_iso_format(end_time)
                # Create chat in Appwrite

                metadata = json.loads(metadata)
                chat_id = metadata['chat_id']
                if chat_id is None:
                    chat = Chat(
                        user_id=user_id,
                        end_time=end_time,
                        start_time=start_time,
                        title=metadata.get('title', session_id),
                        focus_mode=metadata.get('focus_mode', 'default') if metadata else 'default',
                        files=[]  
                    )
                    chat_result = await create_chat(chat)
                else:
                    chat_result = await async_appwrite.get_document(CHAT_COLLECTION_ID, chat_id)
                
                # Retrieve and push messages for this session
                cursor.execute('''
                    SELECT message_type, content, timestamp 
                    FROM session_messages 
                    WHERE session_id = ? 
                    ORDER BY timestamp
                ''', (session_id,))
                messages = cursor.fetchall()
                
                for msg in messages:
                    message_type, content, timestamp = msg
                    message = Message(
                        content=content, 
                        chat_id=chat_result['$id'],
                        message_id=async_appwrite.get_unique_id(),  
                        role=message_type,
                        metadata= str({
                            'original_timestamp': timestamp,
                            'session_id': session_id
                        })
                    )
                    await create_message(message)
                
                # Mark session as synced
                cursor.execute('''
                    UPDATE sessions 
                    SET status = 'synced' 
                    WHERE session_id = ?
                ''', (session_id,))
                
                logger.info(f"Synced session {session_id} to Appwrite")
            
            except Exception as sync_error:
                logger.error(f"Error syncing session {session_id}: {sync_error}")
                # Optionally, mark as failed sync
                cursor.execute('''
                    UPDATE sessions 
                    SET status = 'sync_failed' 
                    WHERE session_id = ?
                ''', (session_id,))
        
        # Commit changes
        conn.commit()
    
    except Exception as e:
        logger.error(f"Error pushing sessions to Appwrite: {e}")
    
    finally:
        # Close database connection
        conn.close()

async def periodic_sync_sessions(interval: int = 3600):
    """
    Periodically sync sessions to Appwrite
    
    Args:
        interval (int): Sync interval in seconds
    """
    import asyncio
    
    while True:
        try:
            await push_sessions_to_appwrite()
        except Exception as e:
            logger.error(f"Periodic sync failed: {e}")
        
        # Wait before next sync
        await asyncio.sleep(interval)

# Optional: Background task to start periodic syncing
# You can call this in your main application startup
async def start_session_sync_task():
    import asyncio
    asyncio.create_task(periodic_sync_sessions())


# def convert_to_iso_format(timestamp):
#     """
#     Convert various timestamp formats to ISO 8601
    
#     Args:
#         timestamp: Input timestamp in various formats
    
#     Returns:
#         str: Timestamp in ISO 8601 format
#     """
#     if isinstance(timestamp, str):
#         try:
#             # Try parsing the existing string format
#             parsed_time = datetime.fromisoformat(timestamp.replace(' ', 'T'))
#         except ValueError:
#             try:
    #                 # Try parsing common datetime formats
#                 parsed_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
#             except ValueError:
#                 # Fallback to current time if parsing fails
#                 parsed_time = datetime.now()
#     elif isinstance(timestamp, datetime):
    #         parsed_time = timestamp
#     else:
    #         # Fallback to current time for unrecognized types
#         parsed_time = datetime.now()
    
#     # Ensure timezone info is added if not present
#     if parsed_time.tzinfo is None:
    #         parsed_time = parsed_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
    
#     return parsed_time.isoformat()