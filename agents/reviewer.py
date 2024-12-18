from .config import agent_manager
from .legacy.base import create_reviewer_agent
from schema import extract_agent_results
from utils.logging import logger
from .state import State
from langgraph.types import Command
from pydantic_ai.result import RunResult


# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.reviewier_agent)
async def reviewer_agent(state: State) -> RunResult:
    try:
        # Safely fetch search results
        if agent_manager.search_agent not in state["agent_results"]:
            raise KeyError("Search agent results not found in state.")
        
        search_result = state["agent_results"][agent_manager.search_agent]
        llm = create_reviewer_agent(search_result)
        response = await llm.run(search_result)
        return response

    except Exception as e:
        logger.error("Failed to execute search agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def reviewer_agent_node(state: State) -> Command[agent_manager.end]:
    try:
        await reviewer_agent(state)
        logger.info("Processed agent results and transitioning to the next node.")
        return Command(goto=agent_manager.end)

    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
