import asyncio
from typing import Literal

from .config import agent_manager
from .search_tool import search_internet_tool
from .legacy.base import create_planner_agent
from schema import extract_agent_results, PlannerAgentSchema
from .state import State
from utils.logging import logger
from utils.exceptions import AgentProcessingError

from langgraph.types import Command
from pydantic_ai.result import RunResult


# Secure meta agent function with proper exception handling
@extract_agent_results(agent_manager.planner_agent)
async def planner_agent(state: State) -> RunResult: 
    try:
        requirements = state["requirements"]
        llm = create_planner_agent()
        # Call LLM with timeout to avoid hanging
        response = await asyncio.wait_for(llm.run(requirements), timeout=10)

        logger.info("Planner agent executed successfully.")
        return response

    except Exception as e:
        logger.error("Unexpected error in meta agent execution.", exc_info=True)
        raise AgentProcessingError("Unexpected error during planner agent execution."+str(e))


# Meta agent node handling logic with validation and exception safety
async def planner_agent_node(state: State, config={}) -> Command[Literal[agent_manager.writer_agent]]:
    try:
        response = await planner_agent(state)
        mode = state["ws_message"]["focus_mode"]
        result: PlannerAgentSchema = response.data
        await search_internet_tool(
                search_query=result.product_retrieval_query,
                description=result.description,
                filter=result.filter,
                n_k=result.n_k,
                mode=mode
        )

        logger.info("Transitioning to writer agent node.")
        return Command(goto=agent_manager.writer_agent, update=state)

    except Exception as e:
        logger.error("Error encountered in planner agent node processing.", exc_info=True)
        raise AgentProcessingError("Unexpected failure in meta agent node.") from e

