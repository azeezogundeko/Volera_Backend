import json
from typing import Literal
from prompts import response_agent_prompt
from schema.validations.agents_schemas import FeedbackResponseSchema

from .state import State
from utils.logging import logger
from utils.helper_state import flatten_history, update_history
from .config import agent_manager
from schema import extract_agent_results
from .legacy.base import create_copilot_agent
from utils.helper_state import get_current_request, stream_final_response

from langgraph.types import Command
from pydantic_ai.result import RunResult
from fastapi import WebSocket


# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.copilot_mode)
async def copilot_agent(state: State, user_input: str = None) -> RunResult:
    try:
        current_request = get_current_request(state)
        query = current_request["message"]["content"]
        history = flatten_history(current_request["history"])
        prompt = response_agent_prompt(history)
        llm = create_copilot_agent(prompt)
        if user_input:
            query = user_input
        response = await llm.run(user_prompt=query)
        return response

    except Exception as e:
        logger.error("Failed to execute copilot agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def copilot_agent_node(state: State) -> Command[Literal[
    agent_manager.planner_agent
]]:
    try:
        user_input = state["human_response"] if "human_response" in state else None
        r = await copilot_agent(state, user_input)
        final: FeedbackResponseSchema = r.data
        if final.action == "__user__":
            state["ai_response"] = final.reply
            state["previous_node"] = agent_manager.copilot_mode
            return Command(goto=agent_manager.human_node, update=state)

        data = final.to_dict()
        requirements = data["requirements"]

        state["ai_response"] = final.reply
        state["previous_node"] = agent_manager.copilot_mode
        state["requirements"] = requirements
            
        # Update history with user input and AI reply
        update_history(
            state, 
            user_input or "", 
            final.reply
        )
        ws: WebSocket = state["ws"]
        await ws.send_json({"type": "message","content": state["ai_response"]})
        await ws.send_json({"type": "messageEnd"})
        state["human_response"] = None
            
        return Command(goto=agent_manager.planner_agent, update=state)

    except Exception as e:
        logger.error("Unexpected error during copilot agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e


async def human_node(
    state: State, config = {}
) -> Command[Literal[
    agent_manager.copilot_mode,
    agent_manager.meta_agent,
    agent_manager.writer_agent,
    agent_manager.search_agent,
    agent_manager.policy_agent,
    ]]:
    try:
        ws: WebSocket = state["ws"]
        
        await stream_final_response(ws,state["ai_response"])

        # Receive and parse the response
        response_text = await ws.receive_text()
        
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
        next_node = state.get("previous_node", agent_manager.end)
        
        logger.info(f"User input collected: {user_input}. Routing to: {next_node}")
        update_history(state, user_input, state["ai_response"])
        return Command(
            update=state,
            goto=next_node
        )

    except Exception as e:
        logger.error(f"Error in human node processing: {e}", exc_info=True)
        raise RuntimeError(f"Interrupt process failed: {e}")
