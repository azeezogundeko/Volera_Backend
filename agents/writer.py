from typing import Literal
from .state import State
from .config import agent_manager
from .legacy.base import create_writer_agent
from schema import extract_agent_results
from prompts import blog_writer_agent_prompt
from utils.logging import logger

from langgraph.types import Command
from pydantic_ai.result import RunResult


# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.writer_agent)
async def writer_agent(state: State) -> RunResult:
    try:
        search_result = state["agent_results"][agent_manager.search_tool]
        instructions = state["agent_results"][agent_manager.meta_agent]["writer_instructions"]
        prompt = blog_writer_agent_prompt(instructions)
        llm = create_writer_agent(prompt)
        response = await llm.run(search_result)
        return response

    except Exception as e:
        logger.error("Failed to execute search agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def writer_agent_node(state: State, config={}) -> Command[Literal[agent_manager.end]]:
    try:
        response = await writer_agent(state)
        request = state["agent_results"][agent_manager.search_tool]
        results = request["results"]
        sources = []
        for r in results:
            sources.append(
                {
                "product_url": r["metadata"]["product_url"],
                "image_url": r["metadata"]["image_url"]
                }
            )

        state["final_result"] = {
            "content":response.data.content, 
            "sources":sources
            }
        logger.info("Processed writer agent results and transitioning to the end node.")
        return Command(goto=agent_manager.end, update=state)

    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
