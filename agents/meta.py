from typing import Literal

from .config import agent_manager
from prompts import meta_prompt
from .legacy.base import create_meta_agent
from schema import extract_agent_results
from .state import State, get_current_request, flatten_history
from utils.logging import logger
from utils.exceptions import AgentInintilaztionError

from langgraph.types import Command
from pydantic_ai.result import RunResult


@extract_agent_results(agent_manager.meta_agent)
async def meta_agent(state: State) -> RunResult: 
    current_request = get_current_request(state)
    query = current_request.message.content
    history = current_request.history
    mapped_history = flatten_history(history)[:5]
    llm = create_meta_agent(meta_prompt(mapped_history))
    response = await llm.run(query)
    return response


async def meta_agent_node(state: State) -> Command[Literal[
    agent_manager.meta_agent,
    agent_manager.shop_agent,
    agent_manager.human_node,
    agent_manager.insights_agent,
    agent_manager.comparison_agent,
]]: 
    response = await meta_agent(state)
    next_node = response.data.next_node

    if next_node == agent_manager.comparison_agent:
        return Command(goto=agent_manager.comparison_agent)
    elif next_node == agent_manager.shop_agent:
        return Command(goto=agent_manager.shop_agent)
    elif next_node == agent_manager.human_node:
        return Command(goto=agent_manager.human_node)
    elif next_node == agent_manager.insights_agent:
        return Command(goto=agent_manager.insights_agent)
    else:
        logger.error(f"Unknown next node: {next_node}")
        raise AgentInintilaztionError(f"Unknown next node: {next_node}")

