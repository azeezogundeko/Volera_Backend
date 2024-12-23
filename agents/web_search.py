from typing import Literal

from .state import State
from utils.logging import logger
from .config import agent_manager
from schema import extract_agent_results
from prompts import web_search_agent_prompt
from .legacy.base import create_web_agent
from utils.helper_state import stream_final_response, get_current_request

from langgraph.types import Command
from pydantic_ai.result import RunResult
from fastapi import WebSocket

# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.web_search_agent)
async def web_agent(state: State, config={}) -> RunResult:
    try:
        # Safely fetch search results
        query = get_current_request(state)["message"]["content"]
        if agent_manager.scrape_mode not in state["agent_results"]:
            raise KeyError("Web agent results not found in state.")
        
        search_result = state["agent_results"][agent_manager.scrape_mode]
        prompt = web_search_agent_prompt(query, search_result)
        llm = create_web_agent(prompt)
        response = await llm.run(query)
        return response

    except Exception as e:
        logger.error("Failed to execute web agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute web agent: {e}")


async def web_agent_node(state: State) -> Command[Literal[agent_manager.end]]:
    try:
        response = await web_agent(state)
        ws: WebSocket = state["ws"]
        result = response.data.content
        sources = []
        for r in results:
            sources.append(
                {
                "product_wurl": r["metadata"]["product_url"],
                "image_url": r["metadata"]["image_url"]
                }
            )
        await ws.send_json({"type": "sources", "content": sources})
        await stream_final_response(state["ws"], result)
        logger.info("Processed Web agent results and transitioning to the next node.")
        return Command(goto=agent_manager.end)


    except Exception as e:
        logger.error("Unexpected error during Web agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
