from typing import Literal

from ..config import agent_manager
from ..human import human_node
from langgraph.types import Command

async def ultra_search_human_node(state, config={}) -> Command[
    Literal[agent_manager.planner_agent,agent_manager.reviewer_agent ,agent_manager.end]
]:
    return await human_node(state, config)