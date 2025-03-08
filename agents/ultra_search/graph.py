from .planner import planner_agent
from .researcher import researcher_agent
from .reviewer import reviewer_agent
from .human_node import ultra_search_human_node
from .response import response_agent

from ..config import agent_manager
from ..state import State

from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

builder = StateGraph(State)

nodes = {
    agent_manager.reviewer_agent: reviewer_agent,
    agent_manager.planner_agent: planner_agent,
    agent_manager.research_agent: researcher_agent,
    agent_manager.human_node: ultra_search_human_node,
    agent_manager.summary_agent: response_agent,
}

for node_name, node_func in nodes.items():
    builder.add_node(node_name, node_func)


builder.set_entry_point(agent_manager.planner_agent)


# # Compile the graph
checkpointer = MemorySaver()
ultra_search_agent_graph = builder.compile(checkpointer=checkpointer)

# async def build_copilot_agent_graph():
#     checkpointer = AsyncMongoDBSaver(async_mongodb_client)
#     return builder.compile(checkpointer=checkpointer)

# async def copilot_agent_graph():
#     return await build_copilot_agent_graph()


