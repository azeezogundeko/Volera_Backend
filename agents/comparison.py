import asyncio
from typing import Literal

from utils.logging import logger
from .config import agent_manager
from prompts import comparison_prompt
from .state import State
from .legacy.base import create_comparison_agent
from utils.exceptions import AgentProcessingError
from schema.dataclass.decourator import extract_agent_results
from utils.helper_state import get_current_request, stream_final_response

from langgraph.types import Command
from pydantic_ai.result import RunResult
from fastapi import WebSocket



# Secure and validated comparison agent function
@extract_agent_results(agent_manager.comparison_agent)
async def comparison_agent(state: State, config={}) -> RunResult:
    try:
        # Safely fetch the current request from state
        current_request = get_current_request(state)
        if not current_request or "message" not in current_request or "content" not in current_request["message"]:
            raise ValueError("Invalid or missing 'content' in current request.")

        # Extract query from the current request
        query = current_request["message"]["content"]
        
        # Safely fetch search results
        if agent_manager.scrape_mode not in state["agent_results"]:
            raise KeyError("Comparison agent results not found in state.")
        
        search_result = state["agent_results"][agent_manager.scrape_mode]
        instructions = state["agent_results"][agent_manager.meta_agent]["instructions"]
        prompt = comparison_prompt(query, search_result, [], instructions)
        llm = create_comparison_agent(prompt)

        response = await asyncio.wait_for(llm.run(query), timeout=10)

        logger.info("Comparison agent successfully executed.")
        return response

    except Exception as e:
        logger.error("Unexpected error during comparison agent execution.", exc_info=True)
        raise AgentProcessingError("Unexpected error occurred." + str(e)) 


# Secure and fault-tolerant meta agent node handling
async def comparison_agent_node(state: State) -> Command[Literal[agent_manager.end]]:
    try:
        # Run the comparison agent safely
        response = await comparison_agent(state)

        ws: WebSocket = state["ws"]
        result = response.data.content
        sources = []
        for r in results:
            sources.append(
                {
                "product_url": r["metadata"]["product_url"],
                "image_url": r["metadata"]["image_url"]
                }
            )
        await ws.send_json({"type": "sources", "content": sources})
        await stream_final_response(state["ws"], result)
        logger.info("Processed Comparisonagent results and transitioning to the next node.")
        return Command(goto=agent_manager.end)


    except Exception as e:
        logger.error("Error encountered in comparison agent node processing.", exc_info=True)
        raise AgentProcessingError("Unexpected failure in meta agent transition.", str(e)) from e
