from datetime import datetime
from .base import async_appwrite
from agents.state import State
from schema.dataclass.database import Chat, Message, MESSAGE_ATTRIBUTES, CHAT_ATTRIBUTES
from utils.logging import logger
from utils.exceptions import DatabaseInintilaztionError

message_collection_id = "messages"
chat_collection_id = "chats"

async def save_chat(state: State):
    chat_id = state["ws_message"]["message"]["chat_id"]
    histories = state["ws_message"]["history"]
    for history in histories:
        message = Message(
            content=history["message"],
            chat_id=chat_id,
            message_id=async_appwrite.unique,
            role=history["speaker"],
            metadata={
                "timestamp": history["timestamp"]
            }
        )
        await create_message(message)


async def create_message(payload: Message):
    return await async_appwrite.create_document(
        message_collection_id,
        payload.__dict__,
        async_appwrite.unique
    )

async def create_chat(payload: Chat):
    return await async_appwrite.create_document(
        chat_collection_id,
        document_data=payload.__dict__,
        document_id=async_appwrite.unique
    )

async def prepare_database():
    try:
        # Chats Collection Preparation
        try:
            await async_appwrite.get_collection(chat_collection_id)
            logger.info('Chats collection already exists')
        except Exception as e:
            logger.warning(f'Attempting to create Chats collection: {e}')
            try:
                # Create collection
                await async_appwrite.create_collection(
                    collection_id=chat_collection_id,
                    name='Chats'
                )
                logger.info('Created Chats collection')

                # Create attributes with robust error handling
                for chat_attribute in CHAT_ATTRIBUTES:
                    try:
                        if chat_attribute.get("type") == "array":
                            await async_appwrite.create_string_attribute(
                                collection_id=chat_collection_id,
                                key=chat_attribute["key"],
                                size=chat_attribute.get("size", 16384),  # Default size for arrays
                                required=chat_attribute.get("required", False),
                                array=True)
                        elif chat_attribute.get("type") == "datetime":
                            await async_appwrite.create_datetime_attribute(
                                collection_id=chat_collection_id,
                                key=chat_attribute["key"],
                                default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                required=chat_attribute.get("required", False))
                        elif chat_attribute.get("type") == "json":
                            await async_appwrite.create_string_attribute(
                                collection_id=chat_collection_id,
                                key=chat_attribute["key"],
                                size=16384,  # Large size for JSON
                                required=chat_attribute.get("required", False))
                        else:
                            await async_appwrite.create_string_attribute(
                                collection_id=chat_collection_id,
                                key=chat_attribute["key"],
                                size=chat_attribute.get("size", 255),
                                required=chat_attribute.get("required", False)
                            )
                        logger.info(f'Created attribute {chat_attribute["key"]} for Chats collection')
                    except Exception as attr_error:
                        logger.error(f'Failed to create attribute {chat_attribute["key"]}: {attr_error}')
                        
            except Exception as create_error:
                logger.error(f'Failed to create Chats collection: {create_error}')
                raise

        # Messages Collection Preparation
        try:
            await async_appwrite.get_collection(message_collection_id)
            logger.info('Messages collection already exists')
        except Exception as e:
            logger.warning(f'Attempting to create Messages collection: {e}')
            try:
                # Create collection
                await async_appwrite.create_collection(
                    collection_id=message_collection_id,
                    name='Messages'
                )
                logger.info('Created Messages collection')

                # Create attributes with robust error handling
                for attr in MESSAGE_ATTRIBUTES:
                    try:
                        if attr.get("type") == "array":
                            await async_appwrite.create_string_attribute(
                                collection_id=message_collection_id,
                                key=attr["key"],
                                size=attr.get("size", 16384),
                                required=attr.get("required", False),
                                array=True)
                        elif attr.get("type") == "datetime":
                            await async_appwrite.create_datetime_attribute(
                                collection_id=message_collection_id,
                                key=attr["key"],
                                default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                required=attr.get("required", False))
                        elif attr.get("type") == "json":
                            await async_appwrite.create_string_attribute(
                                collection_id=message_collection_id,
                                key=attr["key"],
                                size=16384,  # Large size for JSON
                                required=attr.get("required", False))
                        else:
                            await async_appwrite.create_string_attribute(
                                collection_id=message_collection_id,
                                key=attr["key"],
                                size=attr.get("size", 255),
                                required=attr.get("required", False)
                            )
                        logger.info(f'Created attribute {attr["key"]} for Messages collection')
                    except Exception as attr_error:
                        logger.error(f'Failed to create attribute {attr["key"]}: {attr_error}')
                        
            except Exception as create_error:
                logger.error(f'Failed to create Messages collection: {create_error}')
                raise

    except Exception as e:
        logger.error(f'Database initialization failed: {e}')
        raise DatabaseInintilaztionError(str(e))
   