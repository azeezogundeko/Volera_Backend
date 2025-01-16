from datetime import datetime

from utils.logging import logger

from ..auth.services import get_current_user
from ..auth.schema import UserIn
from .model import Chat, Message, SavedChat
from .schema import ChatOut, MessageOut


from fastapi import Depends, Query
from fastapi import HTTPException, APIRouter
from appwrite import query
from appwrite.client import AppwriteException


router = APIRouter()


@router.get("/saved_chats")
async def get_saved_chats(
    limit: int = Query(25),
    page: int = Query(1),
    user: UserIn = Depends(get_current_user)):

    saved_chats = await SavedChat.list([query.Query.equal("user_id", user.id)], limit=limit, offset=(page - 1) * limit)
    chats = []
    
    for c in saved_chats["documents"]:
        chat = await Chat.read(c.chat_id)
        chats.append(chat.to_dict())

    
    return {"message": "Chat starred successfully", "data": chats}


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
async def get_chats(
    limit: int = Query(25),
    page: int = Query(1),
    user: UserIn = Depends(get_current_user)
    ):
    response = await Chat.list([
        query.Query.limit(limit), query.Query.offset((page - 1) * limit), 
        query.Query.order_desc("$createdAt"), 
        query.Query.equal("user_id", user.id)
        ]
    )
    response = {"chats": response["documents"]}
    return response



@router.get("/{chat_id}", response_model=MessageOut)
async def get_chat(chat_id: str, user: UserIn = Depends(get_current_user)):
    # Get the chat document
    try:
        chat = await Chat.read(chat_id)
    except AppwriteException:
        raise HTTPException(status_code=404, detail="Chat not found")
    

    messages = await Message.list([query.Query.equal("chat_id", chat_id)])

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


@router.post("/star_chat")
async def star_chat(chat_id: str, user: UserIn = Depends(get_current_user)):
    try:
        chat = await Chat.read(chat_id)
        await SavedChat.create(document_id=SavedChat.get_unique_id(), data={"chat_id": chat_id})
        return {"message": "Chat starred successfully"}
    except AppwriteException:
        raise HTTPException(status_code=404, detail="Chat not found")


@router.delete("/unstar_chat/{chat_id}")
async def unstar_chat(chat_id: str, user: UserIn = Depends(get_current_user)):
    try:
        saved_chat = await SavedChat.read(chat_id, [query.Query.equal("user_id", user.id)])
        await SavedChat.delete(saved_chat.id)
        return {"message": "Chat unstarred successfully"}
    except AppwriteException:
        raise HTTPException(status_code=404, detail="Chat not found")