from .config import agent_manager
from .legacy.base import create_insights_agent
from schema import extract_agent_results
from utils.logging import logger
from .state import State
from langgraph.types import Command
from pydantic_ai.result import RunResult


# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.insights_agent)
async def insight_agent(state: State) -> RunResult:
    try:
        current_request = get_current_request(state)
        if not current_request or "message" not in current_request or "content" not in current_request["message"]:
            raise ValueError("Invalid or missing 'content' in current request.")

        # Extract query from the current request
        query = current_request["message"]["content"]
        
        # Safely fetch search results
        if agent_manager.search_agent not in state["agent_results"]:
            raise KeyError("Search agent results not found in state.")
        
        search_result = state["agent_results"][agent_manager.search_agent]
        llm = create_insights_agent()
        response = await llm.run(search_result)
        return response

    except Exception as e:
        logger.error("Failed to execute search agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def insights_agent_node(state: State) -> Command[agent_manager.end]:
    try:
        await insight_agent(state)
        logger.info("Processed agent results and transitioning to the next node.")
        return Command(goto=agent_manager.end)

    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
