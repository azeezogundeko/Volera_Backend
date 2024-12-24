from config import SEARCH_ENGINE_URL
from utils.logging import logger
from schema import FilterSchema
from utils.exceptions import NoItemFound

from httpx import AsyncClient


# extract_agent_results(agent_manager.search_tool)
async def search_internet_tool(
    search_query: str,
    filter: FilterSchema,
    n_k: int,
    description: str,
    mode: str
    ):
    async with AsyncClient(timeout=200) as client:  # Set a timeout for all network calls
        # Add the task
        try:
            filter_dict = filter.to_json() if hasattr(filter, 'to_json') else filter
            payload = {
                    "search_query": search_query,
                    "filter": filter_dict,
                    "n_k": n_k,
                    "description": description,
                    "mode": mode,
            }

            request = await client.post(
                SEARCH_ENGINE_URL,
                json=payload,
            )
            if request.status_code != 200:
                logger.error("Error creating request for search", exc_info=True)
                raise NoItemFound("Error creating request for search")
            request = request.json().get("results", [])
   
        except Exception as e:
            logger.error("Error creating request for search", exc_info=True)

        return request