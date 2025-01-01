from typing import Literal
from ..human import human_node
from ..config import agent_manager

from langgraph.types import Command

async def insights_human_node(state: dict, config={})-> Command[Literal[
    agent_manager.web_query_agent,
    agent_manager.followup,
    agent_manager.writer_agent,
     agent_manager.end]]:
    return await human_node(state, config)