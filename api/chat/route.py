from datetime import datetime, timezone, timedelta
from typing import Optional, List

from typing import Literal

from utils.logging import logger
from utils.decorator import auth_required
from utils.search_cache import search_cache_manager

from config import PRODUCTION_MODE
from ..auth.services import get_current_user
from ..auth.schema import UserIn, SearchSuggestion
from .model import Chat, Message, SavedChat, File
from .schema import ChatOut, MessageOut, FileOut

from agents.tools.search import search_tool

from fastapi import Body, Request
from fastapi import Depends, Query, File as FastAPIFile

from fastapi import HTTPException, APIRouter
from fastapi import UploadFile
from appwrite import query
from appwrite.client import AppwriteException
from appwrite.input_file import InputFile
import re


router = APIRouter()

@auth_required
@router.get("/suggestions", response_model=List[SearchSuggestion])
async def get_search_suggestions(
    request: Request,
    query: str = Query(..., min_length=1, description="Search query to get suggestions for"),
    limit: Optional[int] = Query(10, ge=1, le=50, description="Maximum number of suggestions to return")
) -> List[SearchSuggestion]:
    """
    Get search suggestions based on the input query.
    Uses cached search history for suggestions.
    """
    try:

        # Get suggestions from cache
        suggestions = search_cache_manager.get_suggestions(query, limit)
        
        # Convert to SearchSuggestion objects
        return [
            SearchSuggestion(suggestion=suggestion)
            for suggestion in suggestions
        ]

    except Exception as e:
        logger.error(f"Failed to get search suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get search suggestions: {str(e)}"
        )

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

@router.get("/filter")
async def filter_chats(
    dateRange: Literal["all", "today", "week", "month"] = Query(),
    sortBy: Literal["recent", "oldest"] = Query(),
    focusMode: Literal["Q/A" ,"all", "product_hunt"] = Query(),
    user: UserIn = Depends(get_current_user)
):
    # Calculate the date range filter
    current_date = datetime.now(timezone.utc)
    start_date = None

    if dateRange == "today":
        start_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif dateRange == "week":
        start_date = current_date - timedelta(days=current_date.weekday())
    elif dateRange == "month":
        start_date = current_date.replace(day=1)

    # Determine the sorting order
    order_query = query.Query.order_desc("$createdAt") if sortBy == "recent" else query.Query.order_asc("$createdAt")

    filters = [
        query.Query.equal("user_id", user.id),
        query.Query.equal("focus_mode", focusMode)
    ]
    if focusMode == "all":
        filters.pop()

    # Construct the query filters

    if start_date:
        filters.append(query.Query.greater_than_equal("$createdAt", start_date.isoformat()))

    # Execute the query
    response = await Chat.list(filters + [order_query])

    # Prepare the response
    response = {"chats": response["documents"]}
    return response


@router.post("/new", response_model=ChatOut)
async def create_new_chat(
    user: UserIn = Depends(get_current_user)
):
    try:
        chatId = Chat.get_unique_id()
        chat = await Chat.create(
            document_id=chatId,
            data={
                "title": "New Chat",
                "user_id": user.id,
                "start_time": datetime.now().isoformat(),
            }
        )  
        return chat
   
    except Exception as e:
        logger.error(f"Error creating new chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not create chat: {str(e)}")


# Route to get all chats
@router.get("")
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
    messages = await Message.list([query.Query.equal("chat_id", chat_id)])
    
    for message in messages["documents"]:
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


@router.post("/uploads", response_model=FileOut)
async def upload_files(
    files: List[UploadFile] = FastAPIFile(),
    user: UserIn = Depends(get_current_user)
):

    datas = []
    for file in files:
        f = InputFile.from_bytes(
            file.file.read(),
            file.filename
        )
        
        try:
            file = await File.get_or_create(user.id, f, file.filename, file.content_type)
            datas.append(file.to_dict())
        except AppwriteException as e:
            print(str(e))
            # errors.append({"file_name": file.filename, "error": str(e)})
            raise HTTPException(status_code=500, detail="Could not upload file {}".format(file.filename))

    return {"message": "Files uploaded successfully", "files": datas}




