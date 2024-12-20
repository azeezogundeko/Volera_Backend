import time
from typing import TypedDict
from .state import ( 
    TaskInfo, 
    TokenUsage, 
    AgentMetadata,
    Performance, 
    AgentResult, 
    InputOutput,
    )
from typing import Callable
from functools import wraps
from utils.exceptions import AgentInintilaztionError    
from utils.logging import logger

class State(TypedDict):
    ws: dict
    final_result: dict
    chat_limit: int
    chat_finished: bool
    previous_node: str
    previous_search_queries: list
    ws_message: list
    agent_results: dict
    message_history: dict



def extract_agent_results(agent_name: str):
    """
    Decorator to extract agent execution metadata, including timing, tokens, and status.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(state: State, *args, **kwargs) -> AgentResult:
            start_time = time.time()

            # Initialize TaskInfo and TokenUsage
            task_info = TaskInfo(task_id="task_001", status="in_progress", progress=0.0)
            tokens = TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0)
            
            try:
                # Execute the wrapped async function
                response = await func(state, *args, **kwargs)

                cost =  response.cost()
                tokens["input_tokens"] = cost.request_tokens
                tokens["output_tokens"] = cost.response_tokens
                tokens["total_tokens"] = cost.total_tokens

                # Update Task Progress
                # task_info["progress"] = 100.0
                task_info["status"] = "completed"
                
                # Capture execution time
                end_time = time.time()
                execution_time = end_time - start_time

                # Build metadata
                metadata = AgentMetadata(
                    task_info=task_info,
                    performance=Performance(execution_time=execution_time),
                    input_output=InputOutput(tokens=tokens)
                )

                # Build and return AgentResult
                agent_result = AgentResult(
                    name=agent_name,
                    content={"result": response.data},
                    metadata={"metadata": metadata}
                )
                state["agent_results"][agent_name] = agent_result
                state["previous_node"] = agent_name
                return response

            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {str(e)}")
                task_info["status"] = "failed"
                task_info["progress"] = 0.0
                raise AgentInintilaztionError(f"Agent {agent_name} failed: {str(e)}")

        return wrapper
    return decorator