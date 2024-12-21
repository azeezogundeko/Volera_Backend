from typing import Literal

from .config import agent_manager
from utils.logging import logger
from schema import extract_agent_results
from .legacy.base import create_insights_agent
from .state import State
from utils.helper_state import get_current_request

from langgraph.types import Command
from pydantic_ai.result import RunResult


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
        llm = create_insights_agent(search_result)
        response = await llm.run(user_prompt="write a detailed Insights")
        return response

    except Exception as e:
        logger.error("Failed to execute search agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def insights_agent_node(state: State) -> Command[Literal[agent_manager.end]]:
    try:
        await insight_agent(state)
        logger.info("Processed agent results and transitioning to the next node.")
        return Command(goto=agent_manager.end)

    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
