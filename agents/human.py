import json
from typing import Literal

from .state import State
from utils.logging import logger
from utils.helper_state import update_history
from .config import agent_manager
from db.sqlite.manager import session_manager
from utils.websocket import websocket_manager

from langgraph.types import Command
from fastapi import WebSocket


async def human_node(
    state: State, config = {}
) -> Command[Literal[
    agent_manager.planner_agent,
    agent_manager.meta_agent,
    agent_manager.writer_agent,
    ]]:
    try:
        next_node = state.get("next_node", agent_manager.end)
        ws_id = state["ws_id"]
        await websocket_manager.stream_final_response(ws_id, state["ai_response"])
        # await stream_ai_response(ws,state["ai_response"])

        # Receive and parse the response
        response_text = await websocket_manager.receive_json(ws_id)
        
        # Try to parse the response, fallback to raw text
        try:
            response_data = json.loads(response_text)
            user_input = (
                response_data.get('data', {}).get('content') or 
                response_data.get('content') or 
                response_text
            )
        except (json.JSONDecodeError, TypeError):
            user_input = response_text
        
        # Update state with user input
        state["human_response"] = user_input
        
        # Determine next node based on previous context
        
        session_manager.log_message(state["session_id"], 'human', state["human_response"])
        session_manager.log_message(state["session_id"], 'assistant', state["ai_response"])
        update_history(state, user_input, state["ai_response"])
        
        logger.info(f"User input collected: {user_input}. Routing to: {next_node}")
        return Command(
            update=state,
            goto=next_node
        )

    except Exception as e:
        logger.error(f"Error in human node processing: {e}", exc_info=True)
        raise RuntimeError(f"Interrupt process failed: {e}")
