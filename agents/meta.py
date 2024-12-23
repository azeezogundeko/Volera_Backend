import asyncio
from typing import Literal

from .config import agent_manager
from prompts import meta_prompt
from .legacy.base import create_meta_agent
from schema import extract_agent_results, MetaAgentSchema
from utils.helper_state import flatten_history
from .state import State
from utils.logging import logger
from utils.exceptions import AgentProcessingError

from fastapi import WebSocket
from langgraph.types import N, Command
from pydantic_ai.result import RunResult


# Secure meta agent function with proper exception handling
@extract_agent_results(agent_manager.meta_agent)
async def meta_agent(state: State, user_input) -> RunResult: 
    try:
        history = flatten_history(state["ws_message"]["history"], 10)
        prompt = meta_prompt(history)
        llm = create_meta_agent(prompt)
        # Call LLM with timeout to avoid hanging
        response = await asyncio.wait_for(llm.run(user_input), timeout=10)

        logger.info("Meta agent executed successfully.")
        return response

    except Exception as e:
        logger.error("Unexpected error in meta agent execution.", exc_info=True)
        raise AgentProcessingError("Unexpected error during planner agent execution."+str(e))


# Meta agent node handling logic with validation and exception safety
async def meta_agent_node(state: State, config={}) -> Command[Literal[
    agent_manager.writer_agent,
    agent_manager.human_node,
    agent_manager.end
    ]]:
    try:
        user_input = state["human_response"]
        if user_input is None:
            return Command(goto=agent_manager.end, update=state)

        response = await meta_agent(state, user_input)
        result: MetaAgentSchema = response.data
        ws: WebSocket = state["ws"]

        if result.action == "__user__":
            state["ai_response"] = result.content
            state["previous_node"] = agent_manager.meta_agent
            return Command(goto=agent_manager.human_node, update=state)

        await ws.send_json({"type": "message", "content": result.content})
        await ws.send_json({"type": "messageEnd"})
        state["human_response"] = None
        state["requirements"] = result.instructions
        return Command(goto=agent_manager.planner_agent, update=state)

    except Exception as e:
        logger.error("Error encountered in planner agent node processing.", exc_info=True)
        raise AgentProcessingError("Unexpected failure in meta agent node.") from e

