from typing import Literal

from ..config import agent_manager
from ..human import human_node
from langgraph.types import Command


async def web_human_node(state: dict, config={})-> Command[
    Literal[agent_manager.web_query_agent, agent_manager.end]
]:
    return await human_node(state, config)