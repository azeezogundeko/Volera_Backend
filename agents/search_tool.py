from config import SEARCH_ENGINE_URL
from utils.logging import logger
from .config import agent_manager
from schema import extract_agent_results

from httpx import AsyncClient


extract_agent_results(agent_manager.search_tool)
async def search_internet_tool(
    search_query: str,
    filter: str,
    n_k: int,
    description: str,
    mode: str
    ):
    async with AsyncClient(timeout=200) as client:  # Set a timeout for all network calls
        # Add the task
        try:
            payload = {
                    "search_query": search_query,
                    "filter": filter,
                    "n_k": n_k,
                    "description": description,
                    "mode": mode,
            }

            request = await client.post(
                SEARCH_ENGINE_URL,
                json=payload,
            )
            request = request.json().get("results", [])
   
        except Exception as e:
            logger.error("Error creating request for search", exc_info=True)


        return request