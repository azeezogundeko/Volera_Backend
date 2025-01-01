from .human_node import insights_human_node
from ..state import State
from .followup_agent import followup_agent_node
from .web_query_agent import web_query_agent_node
from ..config import agent_manager
from .writer_agent import web_writer_agent_node


from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

builder = StateGraph(State)

nodes = {
    agent_manager.human_node: insights_human_node,
    agent_manager.web_query_agent: web_query_agent_node,
    agent_manager.writer_agent: web_writer_agent_node,
    agent_manager.followup: followup_agent_node,
}

for node_name, node_func in nodes.items():
    builder.add_node(node_name, node_func)

builder.set_entry_point(agent_manager.web_query_agent)


# # Compile the graph
checkpointer = MemorySaver()
insights_agent_graph = builder.compile(checkpointer=checkpointer)
