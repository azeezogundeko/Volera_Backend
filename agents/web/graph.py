from .query_agent import web_query_agent_node
from .writer_agent import web_writer_agent_node
from .human_node import web_human_node
from ..config import agent_manager
from ..state import State

from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

builder = StateGraph(State)

nodes = {
    agent_manager.web_query_agent: web_query_agent_node,
    agent_manager.human_node: web_human_node,
    agent_manager.writer_agent: web_writer_agent_node,
}

for node_name, node_func in nodes.items():
    builder.add_node(node_name, node_func)


builder.set_entry_point(agent_manager.web_query_agent)


# # Compile the graph
checkpointer = MemorySaver()
web_agent_graph = builder.compile(checkpointer=checkpointer)

# async def build_copilot_agent_graph():
#     checkpointer = AsyncMongoDBSaver(async_mongodb_client)
#     return builder.compile(checkpointer=checkpointer)

# async def copilot_agent_graph():
#     return await build_copilot_agent_graph()


