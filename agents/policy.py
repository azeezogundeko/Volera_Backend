import asyncio
from typing import Literal

from utils.logging import logger
from .config import agent_manager
from schema import extract_agent_results
from prompts import policy_prompt
from .legacy.base import create_policy_agent
from .state import State, get_current_request
from utils.exceptions import AgentProcessingError

from langgraph.types import Command
from pydantic_ai.result import RunResult


# Secure meta agent function with proper exception handling
@extract_agent_results(agent_manager.policy_agent)
async def policy_agent(state: State) -> RunResult: 
    try:
        # Safely get the current request and validate the presence of required fields
        current_request = get_current_request(state)
        if not current_request or "message" not in current_request or "content" not in current_request["message"]:
            raise ValueError("Invalid or missing request content.")

        query = current_request["message"]["content"]

        # Prepare the meta agent's prompt and initialize the LLM
        prompt = policy_prompt(query)
        llm = create_policy_agent(prompt)
 
        
        # Call LLM with timeout to avoid hanging
        response = await asyncio.wait_for(llm.run(query), timeout=10)

        logger.info("Meta policy executed successfully.")
        print(response.data)
        return response

    except Exception as e:
        logger.error("Unexpected error in meta agent execution.", exc_info=True)
        raise AgentProcessingError("Unexpected error during meta agent execution.") from e


# Meta agent node handling logic with validation and exception safety
async def policy_agent_node(state: State) -> Command[Literal[
    agent_manager.meta_agent,
    agent_manager.end,
    agent_manager.search_agent
]]:
    try:
        response = await policy_agent(state)

        compliant = response.data.compliant
        if not compliant:
            state["previous_node"] = agent_manager.policy_agent
            return Command(goto=agent_manager.end)
 

        current_request = get_current_request(state)
        if not current_request or "message" not in current_request or "content" not in current_request["message"]:
            raise ValueError("Invalid or missing 'content' in current request.")

        focus_mode = current_request["focus_mode"]
        if focus_mode == agent_manager.copilot_mode:

            logger.info("Transitioning to search agent node.")
            return Command(goto=agent_manager.meta_agent)

        return Command(goto=agent_manager.search_agent)

    except Exception as e:
        logger.error("Error encountered in policy agent node processing.", exc_info=True)
        raise AgentProcessingError("Unexpected failure in meta agent node.") from e
