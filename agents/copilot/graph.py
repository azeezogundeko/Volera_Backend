from .meta_agent import meta_agent_node
from ..state import State
from ..config import agent_manager
from ..human import human_node
from .planner import planner_agent_node
from ..writer import writer_agent_node
from ..followup_agent import followup_agent_node

# from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

builder = StateGraph(State)

nodes = {
    agent_manager.meta_agent: meta_agent_node,
    agent_manager.human_node: human_node,
    agent_manager.followup: followup_agent_node,
    agent_manager.planner_agent: planner_agent_node,
    agent_manager.writer_agent: writer_agent_node,
}

for node_name, node_func in nodes.items():
    builder.add_node(node_name, node_func)


builder.set_entry_point(agent_manager.meta_agent)


# # Compile the graph
checkpointer = MemorySaver()
copilot_agent_graph = builder.compile(checkpointer=checkpointer)

# async def build_copilot_agent_graph():
#     checkpointer = AsyncMongoDBSaver(async_mongodb_client)
#     return builder.compile(checkpointer=checkpointer)

# async def copilot_agent_graph():
#     return await build_copilot_agent_graph()


