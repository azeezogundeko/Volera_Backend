from typing import Literal

from .state import State
from utils.logging import logger
from .config import agent_manager
from schema import extract_agent_results
from prompts import insights_agent_prompt
from .legacy.base import create_insights_agent
from utils.helper_state import get_current_request, stream_final_response

from langgraph.types import Command
from pydantic_ai.result import RunResult
from fastapi import WebSocket


# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.insights_agent)
async def insight_agent(state: State, config={}) -> RunResult:
    try:
        current_request = get_current_request(state)
        if not current_request or "message" not in current_request or "content" not in current_request["message"]:
            raise ValueError("Invalid or missing 'content' in current request.")

        # Extract query from the current request
        query = current_request["message"]["content"]
        
        # Safely fetch search results
        if agent_manager.scrape_mode not in state["agent_results"]:
            raise KeyError("Search agent results not found in state.")
        
        search_result = state["agent_results"][agent_manager.scrape_mode]
        prompts = insights_agent_prompt(query, search_result)
        llm = create_insights_agent(prompts)
        response = await llm.run(user_prompt=query)
        return response

    except Exception as e:
        logger.error("Failed to execute search agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def insights_agent_node(state: State) -> Command[Literal[agent_manager.end]]:
    try:
        response = await insight_agent(state)
        # Get the WebSocket ID from the state
        ws_id = state.get("ws_id")
        if ws_id:
            result = response.data.content
            sources = []
            for r in results:
                sources.append(
                    {
                    "product_url": r["metadata"]["product_url"],
                    "image_url": r["metadata"]["image_url"]
                    }
                )
            await WebSocket(ws_id).send_json({"type": "sources", "content": sources})
            await stream_final_response(ws_id, result)
            logger.info("Processed Insights agent results and transitioning to the next node.")
            return Command(goto=agent_manager.end)

    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
