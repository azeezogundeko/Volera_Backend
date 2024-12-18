import asyncio
from typing import Literal
from httpx import AsyncClient, TimeoutException
from pydantic import ValidationError

from .config import agent_manager
from config import SEARCH_ENGINE_URL
from .legacy.base import create_search_agent
from schema import extract_agent_results, SearchAgentSchema, MetaAgentSchema
from utils.logging import logger
from .state import State
from langgraph.types import Command
from pydantic_ai.result import RunResult


# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.search_agent)
async def search_agent(state: State) -> RunResult:
    try:
        # Safeguard the extraction of instructions
        if "instructions" not in state["agent_results"][agent_manager.meta_agent]:
            raise ValueError("Missing 'instructions' in the state data.")
        
        llm = create_search_agent()
        response = await llm.run(state["agent_results"][agent_manager.meta_agent]["instructions"])
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
        mode = state.get("ws_message", {}).get("optimization_mode", "fast")
        
        # Prepare a list of tasks for concurrent execution with safe HTTP calls
        tasks = []
        async with AsyncClient(timeout=10) as client:  # Set a timeout for all network calls
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
                    task = client.get(
                        SEARCH_ENGINE_URL,
                        params={
                            "query": response_item.query,
                            "filter": response_item.filter,
                            "n_k": response_item.n_k,
                            "semantic_description": response_item.semantic_description,
                            "mode": mode,
                        }
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
            valid_results.append(result)

        # Store the results into state
        state["agent_results"][agent_manager.scrape_mode] = valid_results

        # Ensure MetaAgentSchema parsing is validated
        response: MetaAgentSchema = state["agent_results"].get(agent_manager.meta_agent, {}).get("content", {})
        next_node = response.get("next_node", "__end__")

        # Log successful execution
        logger.info("Processed agent results and transitioning to the next node.")
        return Command(goto=next_node)

    except TimeoutException:
        logger.error("Timeout occurred while querying search engine endpoints.")
        raise RuntimeError("Timeout occurred while querying search engine.")
    except ValidationError as ve:
        logger.error("Validation error occurred in response processing.", exc_info=True)
        raise RuntimeError("Invalid data returned from search agent.") from ve
    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
