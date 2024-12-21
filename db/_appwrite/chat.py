from datetime import datetime
from .base import async_appwrite
from schema.dataclass.database import Chat, Message, MESSAGE_ATTRIBUTES, CHAT_ATTRIBUTES
from utils.logging import logger
from utils.exceptions import DatabaseInintilaztionError

message_collection_id = "messages"
chat_collection_id = "chats"

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
            # Try to get the collection to check if it exists
            await async_appwrite.get_collection(chat_collection_id)
            logger.info('Chats collection already exists')
        except Exception as e:
            # If collection doesn't exist, create it
            if 'collection (404)' in str(e):
                await async_appwrite.create_collection(
                    collection_id=chat_collection_id,
                    name='Chats'
                )
                # Create Chats Collection
                for chat_attribute in CHAT_ATTRIBUTES:
                    if chat_attribute.get("type") == "array":
                        await async_appwrite.create_string_attribute(
                            collection_id=chat_collection_id,
                            key=chat_attribute["key"],
                            size=chat_attribute["size"],
                            required=chat_attribute["required"],
                            array=True)
                    elif chat_attribute.get("type") == "datetime":
                        await async_appwrite.create_datetime_attribute(
                            collection_id=chat_collection_id,
                            key=chat_attribute["key"],
                            default=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                            required=chat_attribute["required"])
                    else:
                        await async_appwrite.create_string_attribute(
                            chat_collection_id,
                            key=chat_attribute["key"],
                            size=chat_attribute["size"],
                            required=chat_attribute["required"]
                            )
                        
                logger.info('Created Chats collection with attributes')
            else:
                raise

        # Messages Collection Preparation
        try:
            # Try to get the collection to check if it exists
            await async_appwrite.get_collection(message_collection_id)
            logger.info('Messages collection already exists')
        except Exception as e:
            # If collection doesn't exist, create it
            if 'collection (404)' in str(e):
                await async_appwrite.create_collection(
                    collection_id=message_collection_id,
                    name='Messages'
                )
                for attr in MESSAGE_ATTRIBUTES:
                    if attr.get("type") == "array":
                        await async_appwrite.create_string_attribute(
                            collection_id=message_collection_id,
                            key=attr["key"],
                            size=attr["size"],
                            required=attr["required"],
                            array=True)
                    elif attr.get("type") == "datetime":
                        await async_appwrite.create_datetime_attribute(
                            collection_id=message_collection_id,
                            key=attr["key"],
                            default=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                            required=attr["required"])
                    else:
                        await async_appwrite.create_string_attribute(
                            message_collection_id,
                            key=attr["key"],
                            size=attr["size"],
                            required=attr["required"]
                            )

                logger.info('Created Messages collection with attributes')
            else:
                raise

    except Exception as e:
        raise DatabaseInintilaztionError(str(e))