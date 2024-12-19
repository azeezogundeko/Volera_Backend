from typing import Literal
import asyncio

from .config import agent_manager
from prompts import meta_prompt
from .legacy.base import create_meta_agent
from schema import extract_agent_results
from .state import State, get_current_request, flatten_history
from utils.logging import logger
from utils.exceptions import AgentProcessingError, AgentInintilaztionError

from langgraph.types import Command
from pydantic_ai.result import RunResult


# Secure meta agent function with proper exception handling
@extract_agent_results(agent_manager.meta_agent)
async def meta_agent(state: State) -> RunResult: 
    try:
        # Safely get the current request and validate the presence of required fields
        current_request = get_current_request(state)
        if not current_request or "message" not in current_request or "content" not in current_request["message"]:
            raise ValueError("Invalid or missing request content.")

        query = current_request["message"]["content"]
        history = current_request.get("history", [])
        
        # Flatten and slice history safely
        mapped_history = flatten_history(history)
        
        # Prepare the meta agent's prompt and initialize the LLM
        prompt = meta_prompt(mapped_history)
        llm = create_meta_agent(prompt)
        
        # Call LLM with timeout to avoid hanging
        response = await asyncio.wait_for(llm.run(query), timeout=10)

        logger.info("Meta agent executed successfully.")
        return response

    except Exception as e:
        logger.error("Unexpected error in meta agent execution.", exc_info=True)
        raise AgentProcessingError("Unexpected error during meta agent execution.") from e


# Meta agent node handling logic with validation and exception safety
async def meta_agent_node(state: State) -> Command[Literal[
    agent_manager.search_agent,
    agent_manager.end,
]]:
    try:
        # Fetch all agents safely
        all_agents = agent_manager.get_all_agents()

        # Call the meta agent function
        response = await meta_agent(state)
        print(response.data)
        
        # Ensure response is valid
        if not response:
            logger.error("Invalid response from meta agent.")
            raise AgentInintilaztionError("No valid next node found in meta agent response.")

        next_node = response.data.next_node

        # Log and handle unrecognized next nodes
        if next_node not in all_agents:
            logger.error(f"Unknown next node: {next_node}")
            raise AgentInintilaztionError(f"Unknown next node: {next_node}")

        # Decide the next state transition based on next_node value
        if next_node == agent_manager.human_node:
            logger.info("Transitioning to human node.")
            return Command(goto=agent_manager.end)
        
        logger.info("Transitioning to search agent node.")
        return Command(goto=agent_manager.search_agent)

    except Exception as e:
        logger.error("Error encountered in meta agent node processing.", exc_info=True)
        raise AgentProcessingError("Unexpected failure in meta agent node.") from e
