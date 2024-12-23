from agents import (
    agent_manager,
    State,
    planner_agent_node, 
    search_agent_node, 
    comparison_agent_node, 
    reviewer_agent_node, 
    policy_agent_node, 
    insights_agent_node,
    copilot_agent_node,
    human_node,
    meta_agent_node,
    writer_agent_node,
    web_agent_node
)

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph


# Define node mapping with error handling
nodes = {
    agent_manager.comparison_agent: comparison_agent_node,
    agent_manager.insights_agent: insights_agent_node,
    agent_manager.reviewer_agent: reviewer_agent_node,
    agent_manager.planner_agent: planner_agent_node,
    agent_manager.copilot_mode: copilot_agent_node,
    agent_manager.web_search_agent: web_agent_node,
    agent_manager.search_agent: search_agent_node,
    agent_manager.writer_agent: writer_agent_node,
    agent_manager.policy_agent: policy_agent_node,
    agent_manager.meta_agent: meta_agent_node,
    agent_manager.human_node: human_node,
}

# Create state graph with robust configuration
builder = StateGraph(State)

# Add nodes to the graph
for node_name, node_func in nodes.items():
    builder.add_node(node_name, node_func)

# Set entry point
builder.set_entry_point(agent_manager.copilot_mode)

# Compile the graph
checkpointer = MemorySaver()
agent_graph = builder.compile(checkpointer=checkpointer)

