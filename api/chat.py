from db import async_appwrite
from appwrite.query import Query
from utils.logging import logger
from db._appwrite.chat import chat_collection_id, message_collection_id

from fastapi import HTTPException, APIRouter

router = APIRouter()

# Route to get all chats
@router.get("/")
async def get_chats():
    response = await async_appwrite.list_documents(
        chat_collection_id,
        queries=[Query.order_desc("$createdAt")]
    )
    return {"chats": response["documents"]}

# Route to get specific chat by ID
@router.get("/{chat_id}")
async def get_chat(chat_id: str):
    # Get the chat document
    chat_exists = await async_appwrite.get_document(
        chat_collection_id, 
        chat_id)
    
    # If the chat doesn't exist, return a 404 error
    if not chat_exists:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Get all messages related to the chat
    chat_messages = await async_appwrite.list_documents(
        chat_collection_id,
        queries=[Query.equal("chatId", chat_id)]
    )

    return {"chat": chat_exists, "messages": chat_messages["documents"]}

# Route to delete a chat by ID
@router.delete("/{chat_id}")
async def delete_chat(chat_id: str):

    # Delete chat document
    await async_appwrite.delete_document(chat_collection_id, chat_id)

    # Get all related messages and delete them
    messages = await async_appwrite.list_documents(
        message_collection_id,
        queries=[Query.equal("chatId", chat_id)]
    )
    
    # Delete each message document
    for message in messages["documents"]:
        await async_appwrite.delete_document(message, message["$id"])

    return {"message": "Chat deleted successfully"}
