import asyncio
# from pprint import pprint
from typing import Literal
from httpx import AsyncClient, TimeoutException

from utils.exceptions import AgentProcessingError

from .config import agent_manager
from config import SEARCH_ENGINE_URL
from .legacy.base import create_search_agent
from schema import extract_agent_results, SearchAgentSchema
from utils.logging import logger
from .state import State
from utils.helper_state import get_current_request
from langgraph.types import Command
from pydantic_ai.result import RunResult


# Secure wrapper to handle agent responses safely
@extract_agent_results(agent_manager.search_agent)
async def search_agent(state: State, focus_mode: str) -> RunResult:
    try:
        current_request = get_current_request(state)
        user_query = current_request["message"]["content"]
        query = f"""
                User Query:
                    {user_query}

                Focus Mode:
                    {focus_mode}
        """
        llm = create_search_agent()
        response = await llm.run(query)
        return response

    except Exception as e:
        logger.error("Failed to execute search agent operation", exc_info=True)
        raise RuntimeError(f"Failed to execute search agent: {e}")


async def search_agent_node(state: State) -> Command[Literal[
    agent_manager.comparison_agent,
    agent_manager.insights_agent,
    agent_manager.reviewer_agent,
    agent_manager.web_search_agent
]]:
    try:
        # Call the search agent
        current_request = get_current_request(state)
        focus_mode = current_request.get("focus_mode", agent_manager.web_search_mode)
        response = await search_agent(state, focus_mode)

        # Validate the response data
        if not response or not response.data:
            raise ValueError("No valid data returned by search agent.")

        responses: SearchAgentSchema = response.data
        
        mode = current_request.get("optimization_mode", "fast")
        # Prepare a list of tasks for concurrent execution with safe HTTP calls
        tasks = []
        async with AsyncClient(timeout=200) as client:  # Set a timeout for all network calls
            for response_item in responses.param:
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
                            "search_strategy": response_item.search_strategy,
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

        if focus_mode == agent_manager.comparison_mode:
            next_node = agent_manager.comparison_agent        
        elif focus_mode == agent_manager.insights_mode:
            next_node = agent_manager.insights_agent
        elif focus_mode == agent_manager.review_mode:
            next_node = agent_manager.reviewer_agent  
        else: 
            next_node = agent_manager.web_search_agent

        # Log successful execution
        logger.info("Processed agent results and transitioning to the next node.")
        return Command(goto=next_node, update=state)

    except TimeoutException:
        logger.error("Timeout occurred while querying search engine endpoints.")
        raise RuntimeError("Timeout occurred while querying search engine.")
    except Exception as e:
        logger.error("Unexpected error during search agent node processing.", exc_info=True)
        raise RuntimeError("Unexpected error occurred.") from e
