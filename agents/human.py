import json
import asyncio
from typing import Literal

from .state import State
from utils.logging import logger
from utils.helper_state import update_history
from .config import agent_manager
from db._appwrite.session import appwrite_session_manager
from utils.websocket import websocket_manager

from langgraph.types import Command
from pydantic import BaseModel

class FileMessage(BaseModel):
    fileData: bytes
    fileName: str
    fileExtension: str

async def extract_message_content(response_text: str) -> str:
    """Extract the message content from the response text."""
    try:
        # Handle string input
        if isinstance(response_text, str):
            # Try to parse as JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                return response_text

            # Handle dictionary
        
            if isinstance(data, dict):
                # Try nested data structure
                if 'data' in data and isinstance(data['data'], dict):
                    return data['data'].get('content', '')
                # Try direct content
                if 'content' in data:
                    return data['content']
                # Try message field
                if 'message' in data:
                    return data['message']

                # if 'files' in data:
                #     ...
                
        # Handle dictionary input
        elif isinstance(response_text, dict):
            if 'data' in response_text and isinstance(response_text['data'], dict):
                return response_text['data'].get('content', '')
            return response_text.get('content', str(response_text))
            
    except Exception as e:
        logger.error(f"Error extracting message content: {e}", exc_info=True)
        return str(response_text)
    
    return str(response_text)


async def human_node(
    state: State,
    config = {}
) -> Command[Literal[
    agent_manager.planner_agent,
    agent_manager.meta_agent,
    agent_manager.writer_agent,
]]:
    try:
        next_node = state.get("next_node", agent_manager.end)
        ws_id = state["ws_id"]

        # if "ai_response" in state:
        # state["message_data"] = None
        
        # Receive user input with retries
        max_retries = 3
        retry_delay = 3
        response_text = None
        
        # update_history(state, state["human_response"], state["ai_response"])
        # response_text = await websocket_manager.receive_json(ws_id)

        for attempt in range(max_retries):
            try:
                response_text = await websocket_manager.receive_json(ws_id)
                if response_text:
                    break
                await asyncio.sleep(retry_delay)
                logger.warning(f"Empty response on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Error receiving message (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        if not response_text:
            await websocket_manager.send_error_response(ws_id, "Failed to receive user input", "USER_INPUT_ERROR")
            return Command(goto=agent_manager.end, update=state)
            # raise RuntimeError("Failed to receive user input after multiple attempts")
        
        # Extract user input from response
        user_input = await extract_message_content(response_text)
        if not user_input:
            await websocket_manager.send_error_response(ws_id, "Failed to receive user input", "USER_INPUT_ERROR")
            return Command(goto=agent_manager.end, update=state)
            # raise ValueError("Failed to extract valid user input from response")

        # user_images = await appwrite_session_manager._process_files(user_files)
        await appwrite_session_manager.log_message(state["human_response"], state["session_id"], 'human')
        
        # Update state with the user's input
        state["human_response"] = user_input
     
        logger.info(f"User input collected: {user_input}. Routing to: {next_node}")
        return Command(update=state, goto=next_node)

    except Exception as e:
        logger.error(f"Error in human node: {str(e)}", exc_info=True)
        state["error"] = str(e)
        return Command(goto=agent_manager.end, update=state)