from typing import Literal
from .config import agent_manager
from .legacy.base import create_reviewer_agent
from schema import extract_agent_results
from prompts import reviewer_agent_prompt
from utils.logging import logger
from .state import State
from langgraph.types import Command
from pydantic_ai.result import RunResult


# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.reviewer_agent)
async def reviewer_agent(state: State) -> RunResult:
    try:
        # Safely fetch search results
        if agent_manager.scrape_mode not in state["agent_results"]:
            raise KeyError("Reviewer agent results not found in state.")
        
        # instructions = state["agent_results"][agent_manager.meta_agent]["instructions"]
        search_result = state["agent_results"][agent_manager.scrape_mode]
        prompt = reviewer_agent_prompt(search_result)
        llm = create_reviewer_agent(prompt)
        response = await llm.run("write a detailed review")
        print(response.data)
        return response

    except Exception as e:
        logger.error("Failed to execute search agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def reviewer_agent_node(state: State) -> Command[Literal[agent_manager.end]]:
    try:
        await reviewer_agent(state)
        logger.info("Processed agent results and transitioning to the next node.")
        return Command(goto=agent_manager.end)

    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
