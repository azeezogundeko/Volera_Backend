import asyncio
# from pprint import pprint
from typing import Literal
from httpx import AsyncClient, TimeoutException

from utils.exceptions import AgentProcessingError

from .config import agent_manager
from config import SEARCH_ENGINE_URL
from .legacy.base import create_search_agent
from schema import extract_agent_results, SearchAgentSchema, MetaAgentSchema
from utils.logging import logger
from .state import State, get_current_request
from langgraph.types import Command
from pydantic_ai.result import RunResult


# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.search_agent)
async def search_agent(state: State) -> RunResult:
    try:
        # Safeguard the extraction of instructions
        if "instructions" not in state["agent_results"][agent_manager.meta_agent]:
            raise ValueError("Missing 'instructions' in the state data.")

        current_request = get_current_request(state)
        focus_mode = current_request["focus_mode"]
        if focus_mode == agent_manager.copilot_mode:
            instructions = state["agent_results"][agent_manager.meta_agent]["instructions"]
            llm = create_search_agent()
            response = await llm.run(instructions)
            return response

        current_request = get_current_request(state)
        query = current_request["message"]["content"]

        llm = create_search_agent()
        response = await llm.run(query)
        return response

    except Exception as e:
        logger.error("Failed to execute search agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def search_agent_node(state: State) -> Command[Literal[
    agent_manager.comparison_agent,
    agent_manager.insights_agent,
    agent_manager.reviewer_agent
]]:
    try:
        # Call the search agent
        response = await search_agent(state)

        # Validate the response data
        if not response or not response.data:
            raise ValueError("No valid data returned by search agent.")

        responses: SearchAgentSchema = response.data
        current_request = get_current_request(state)
        mode = current_request.get("optimization_mode", "fast")
        
        # Prepare a list of tasks for concurrent execution with safe HTTP calls
        tasks = []
        async with AsyncClient(timeout=200) as client:  # Set a timeout for all network calls
            for response_item in responses.params:
                # Validate query parameters to avoid injection
                if not isinstance(response_item.query, str) or not response_item.query.strip():
                    logger.warning(f"Skipping invalid or empty query: {response_item.query}")
                    continue

                # Ensure filters are properly validated
                if not isinstance(response_item.filter, str):
                    logger.warning(f"Skipping invalid filter: {response_item.filter}")
                    continue

                # Add the task
                try:
                    payload = {
                            "search_query": response_item.query,
                            "filter": response_item.filter,
                            "n_k": response_item.n_k,
                            "description": response_item.semantic_description,
                            "mode": mode,
                    }

                    task = client.post(
                        SEARCH_ENGINE_URL,
                        json=payload,
                    )
                    tasks.append(task)
                except Exception as e:
                    logger.error("Error creating request for search", exc_info=True)

            # Execute all tasks concurrently
            search_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle failed requests safely
        valid_results = []
        for result in search_results:
            if isinstance(result, Exception):
                logger.error("HTTP request failed", exc_info=True)
                continue
            valid_results.extend(result.json().get("results", []))

        # Store the results into state
        state["agent_results"][agent_manager.scrape_mode] = valid_results
        # pprint(valid_results)
        current_request = get_current_request(state)
        focus_mode = current_request["focus_mode"]

        if focus_mode == agent_manager.copilot_mode:
            response: MetaAgentSchema = state["agent_results"].get(agent_manager.meta_agent, {}).get("content", {})
            next_node = response.get("next_node", "__end__")
        elif focus_mode == agent_manager.comparison_mode:
            next_node = agent_manager.comparison_agent        
        elif focus_mode == agent_manager.insights_mode:
            next_node = agent_manager.insights_agent
        elif focus_mode == agent_manager.review_mode:
            next_node = agent_manager.reviewer_agent  
        else: 
            raise AgentProcessingError("Focus mode is not valid  "+ focus_mode)

        # Log successful execution
        logger.info("Processed agent results and transitioning to the next node.")
        return Command(goto=next_node)

    except TimeoutException:
        logger.error("Timeout occurred while querying search engine endpoints.")
        raise RuntimeError("Timeout occurred while querying search engine.")
    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
