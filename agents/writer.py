from typing import Literal

from fastapi import WebSocket
from .state import State
from .config import agent_manager
from .tools.markdown import convert_to_markdown
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
        print(search_result)
        instructions = state["agent_results"][agent_manager.planner_agent]["content"]["writer_instructions"]
        prompt = blog_writer_agent_prompt(str(instructions))
        llm = create_writer_agent(prompt)
        contents = [r["content"] for r in search_result]
        response = await llm.run(str(contents))
        return response

    except Exception as e:
        logger.error("Failed to execute search agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def writer_agent_node(state: State, config={}) -> Command[Literal[agent_manager.end]]:
    try:
        response = await writer_agent(state)
        content = convert_to_markdown(response.data.content)
        ws: WebSocket = state["ws"]
        search_results = state["agent_results"][agent_manager.search_tool]
        #meta agent will reply to follow up questions
        state["previous_node"] = agent_manager.meta_agent

        sources = []
        for r in search_results:
            source_data = {
                "product_url": r["metadata"].get("product_url", ""),
                "image_url": r["metadata"].get("image_url", ""),
                # "title": r["metadata"].get("title", "")
            }
            sources.append(source_data)
        
        # Send sources with comprehensive data
        await ws.send_json({
            "type": "sources", 
            "content": {
                "sources": sources,
                "message_id": state["ws_message"]["message"]["message_id"]
            }
        })

        state["ai_response"] = content
        logger.info("Processed writer agent results and transitioning to the end node.")
        return Command(goto=agent_manager.human_node, update=state)

    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
