from agents import (
    agent_manager,
    State,
    meta_agent_node, 
    search_agent_node, 
    comparison_agent_node, 
    reviewer_agent_node, 
    policy_agent_node, 
    insights_agent_node
)

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.graph import CompiledGraph


def create_agent_graph() -> CompiledGraph:
    try:
        # Define node mapping with error handling
        nodes = {
            agent_manager.meta_agent: meta_agent_node,
            agent_manager.search_agent: search_agent_node,
            agent_manager.comparison_agent: comparison_agent_node,
            agent_manager.policy_agent: policy_agent_node,
            agent_manager.insights_agent: insights_agent_node,
            agent_manager.reviewer_agent: reviewer_agent_node,
        }

        # Create state graph with robust configuration
        builder = StateGraph(State)

        # Add nodes to the graph
        for node_name, node_func in nodes.items():
            builder.add_node(node_name, node_func)

        # Set entry point
        builder.set_entry_point(agent_manager.policy_agent)

        # Compile the graph
        checkpointer = MemorySaver()
        agent_graph = builder.compile(checkpointer=checkpointer)
        
        return agent_graph

    except Exception as e:
        # Log graph creation error
        from utils.logging import logger
        logger.error(f"Error creating agent graph: {e}", exc_info=True)
        raise

# Create the agent graph instance
agent_graph = create_agent_graph()