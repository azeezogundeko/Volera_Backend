from datetime import datetime
from typing import List, Optional

from db import async_appwrite
from appwrite.query import Query
from utils.logging import logger
from db._appwrite.chat import create_chat, create_message
from schema.dataclass.database import Chat, Message, File
from config import CHAT_COLLECTION_ID, MESSAGE_COLLECTION_ID

from fastapi import Body
from fastapi import HTTPException, APIRouter


router = APIRouter()


@router.post("/new")
async def create_new_chat(
    user_id: str = Body(...),
    title: Optional[str] = Body(None),
    focus_mode: str = Body("default", alias="focusMode"),
    files: Optional[List[dict]] = Body(None)
):
    """
    Create a new chat for a user.
    
    Args:
        user_id (str): ID of the user creating the chat
        title (str, optional): Title of the chat
        focus_mode (str, optional): Focus mode for the chat
        files (List[dict], optional): List of files associated with the chat
    
    Returns:
        dict: Created chat details
    """
    try:
        # Generate a default title if not provided
        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Convert files to File objects if provided
        parsed_files = [File(**file) for file in files] if files else []
        
        # Create chat
        chat = Chat(
            title=title,
            focus_mode=focus_mode,
            files=parsed_files
        )
        
        # Save chat to database
        chat_result = await create_chat(chat)
        
        return {
            "chat_id": chat_result['$id'],
            "title": title,
            "focus_mode": focus_mode
        }
    
    except Exception as e:
        logger.error(f"Error creating new chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not create chat: {str(e)}")

@router.post("/{chat_id}/end")
async def end_chat_session(
    chat_id: str, 
    final_messages: Optional[List[dict]] = Body(None)
):
    """
    End a chat session and save final messages.
    
    Args:
        chat_id (str): ID of the chat to end
        final_messages (List[dict], optional): Messages to save at end of session
    
    Returns:
        dict: Status of chat session ending
    """
    try:
        # Update chat status to 'completed'
        await async_appwrite.update_document(
            chat_collection_id, 
            chat_id, 
            {"status": "completed"}
        )
        
        # Save final messages if provided
        if final_messages:
            for msg in final_messages:
                message = Message(
                    content=msg.get('content', ''),
                    chat_id=chat_id,
                    message_id='',  # Will be auto-generated
                    role=msg.get('role', 'assistant'),
                    metadata=msg.get('metadata', {})
                )
                await create_message(message)
        
        return {
            "status": "success", 
            "message": "Chat session ended",
            "chat_id": chat_id
        }
    
    except Exception as e:
        logger.error(f"Error ending chat session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not end chat session: {str(e)}")
















# Route to get all chats
@router.get("/")
async def get_chats():
    response = await async_appwrite.list_documents(
        CHAT_COLLECTION_ID,
        queries=[Query.order_desc("$createdAt")]
    )
    response = {"chats": response["documents"]}
    return response

def format_to_markdown(content):
    import re

    formatted_content = content.replace('\\n', '\n')
    
    # Optional: Additional markdown cleanup and formatting
    # Remove any excessive whitespace
    formatted_content = re.sub(r'\n{3,}', '\n\n', formatted_content)
    
    # Ensure consistent list formatting
    formatted_content = re.sub(r'^(\s*)\*\s*', r'\1- ', formatted_content, flags=re.MULTILINE)
    print(formatted_content)
    
    return formatted_content

def format_dt(data):
    for message in data['messages']:
        original_content = message.get('content', '')
        markdown_content = format_to_markdown(original_content)
        message['formatted_markdown'] = markdown_content

    return data

# Route to get specific chat by ID
@router.get("/{chat_id}")
async def get_chat(chat_id: str):
    # Get the chat document
    chat_exists = await async_appwrite.get_document(
        CHAT_COLLECTION_ID, 
        chat_id)
    
    # If the chat doesn't exist, return a 404 error
    if not chat_exists:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Get all messages related to the chat
    chat_messages = await async_appwrite.list_documents(
        MESSAGE_COLLECTION_ID,  # Use the correct collection for messages
        queries=[Query.equal("chat_id", chat_id)]
    )

    response = {
        "chat": chat_exists, 
        "messages": chat_messages["documents"]
    }
    return format_dt(response)

# Route to delete a chat by ID
@router.delete("/{chat_id}")
async def delete_chat(chat_id: str):

    # Delete chat document
    await async_appwrite.delete_document(CHAT_COLLECTION_ID, chat_id)

    # Get all related messages and delete them
    messages = await async_appwrite.list_documents(
        MESSAGE_COLLECTION_ID,
        queries=[Query.equal("chatId", chat_id)]
    )
    
    # Delete each message document
    for message in messages["documents"]:
        await async_appwrite.delete_document(message, message["$id"])

    return {"message": "Chat deleted successfully"}
