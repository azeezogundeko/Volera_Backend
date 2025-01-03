from datetime import datetime

from utils.logging import logger

from ..auth.services import get_current_user
from ..auth.schema import UserIn
from .model import Chat, Message, File
from .schema import ChatOut, MessageOut


from fastapi import Depends
from fastapi import HTTPException, APIRouter
from appwrite.query import Query
from appwrite.client import AppwriteException


router = APIRouter()


@router.post("/new", response_model=ChatOut)
async def create_new_chat(
    user: UserIn = Depends(get_current_user)
):
    try:
        return await Chat.create(
            document_id=Chat.get_unique_id(),
            data={
                "title": "New Chat",
                "user_id": user.id,
                "start_time": datetime.now().isoformat(),
            }
        )

        
   
    except Exception as e:
        logger.error(f"Error creating new chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not create chat: {str(e)}")



# Route to get all chats
@router.get("/")
async def get_chats(user: UserIn = Depends(get_current_user)):
    response = await Chat.list([Query.order_desc("$createdAt"), Query.equal("user_id", user.id)])
    response = {"chats": response["documents"]}
    return response



@router.get("/{chat_id}", response_model=MessageOut)
async def get_chat(chat_id: str, user: UserIn = Depends(get_current_user)):
    # Get the chat document
    try:
        chat = await Chat.read(chat_id)
    except AppwriteException:
        raise HTTPException(status_code=404, detail="Chat not found")
    

    messages = await Message.list([Query.equal("chat_id", chat_id)])

    response = {
        "chat": chat, 
        "messages": messages
    }

    return response


@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, user: UserIn = Depends(get_current_user)):
    try:
        await Chat.delete(chat_id)
    except AppwriteException:
        return 
    # Get all related messages and delete them
    messages = await Message.list([Query.equal("chat_id", chat_id)])
    
    for message in messages:
        await Message.delete(message.id)

    return {"message": "Chat deleted successfully"}
