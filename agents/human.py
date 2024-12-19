# from typing import Dict, Any
# from langgraph.types import Command, interrupt
# from schema import History, Result, GroqDependencies
# from .legacy.base import agent_manager
# from pydantic_ai import Agent
# from utils.logging import logger
# from utils.exceptions import AgentProcessingError

# system_prompt = """
# You are a helpful and professional assistant representing a company. 
# When addressing issues or requests forwarded by another agent:

# 1. **For Insufficient Requirements**:
#    If the forwarded request lacks necessary details, politely ask the originating agent to provide the missing information.

# 2. **For Policy Violations**:
#    If the forwarded request violates a company policy, politely inform the originating agent of the violation.

# 3. **For Clear and Compliant Requests**:
#    If the forwarded request is clear and complies with policies, provide a concise response.

# 4. **Response Format**:
#    Always respond in valid JSON format with keys: 'type' and 'content'
# """

# human_response_agent = Agent(
#     name="human_response_agent",
#     model="groq:llama3-70b-8192",
#     system_prompt=system_prompt,
#     result_type=Result,
#     deps_type=GroqDependencies,
#     retries=2
# )

# async def human_node(state: Dict[str, Any], config: Dict[str, Any]) -> Command:
#     """
#     Handle human interaction node in the agent workflow.
    
#     Args:
#         state (Dict[str, Any]): Current agent state
#         config (Dict[str, Any]): Configuration for the current execution
    
#     Returns:
#         Command: Next agent node to execute
#     """
#     try:
#         # Validate configuration and triggers
#         if not config or 'metadata' not in config:
#             raise AgentProcessingError("Invalid configuration")
        
#         langgraph_triggers = config.get('metadata', {}).get('langgraph_triggers', [])
        
#         if len(langgraph_triggers) != 1:
#             logger.warning(f"Unexpected number of triggers: {len(langgraph_triggers)}")
#             raise AgentProcessingError("Expected exactly 1 trigger in human node")

#         # Extract active agent safely
#         active_agent_trigger = langgraph_triggers[0]
#         active_agent = active_agent_trigger.split(":")[-1] if ":" in active_agent_trigger else active_agent_trigger

#         # Safely retrieve agent response
#         agent_results = state.get('agent_results', {})
#         agent_response = agent_results.get(active_agent, {})
        
#         if not agent_response:
#             logger.error(f"No response found for agent: {active_agent}")
#             raise AgentProcessingError(f"Missing agent response for {active_agent}")

#         # Process response using human response agent
#         interrupt_result = await human_response_agent.run(agent_response.get('content', ''))
        
#         # Prepare user interaction
#         user_input = interrupt(value=interrupt_result)
        
#         # Update history safely
#         history = state.get('message_history', [])
#         history.extend([
#             History(speaker="assistant", message=agent_response.get('content', '')),
#             History(speaker="human", message=str(user_input))
#         ])
        
#         # Update state with new history
#         state['message_history'] = history

#         # Return command to revisit the active agent
#         return Command(
#             goto=active_agent,
#             config={"resume": user_input}
#         )

#     except Exception as e:
#         logger.error(f"Error in human node: {e}", exc_info=True)
#         raise AgentProcessingError("Unexpected error in human interaction") from e