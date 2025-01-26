from typing import List, Dict, Any

from schema import GeminiDependencies
# from api.product.schema import ProductResponse
from .prompts import filter_agent_prompt

from pydantic_ai import Agent
from pydantic import Field

class FilterSchema(BaseModel):
    product_ids: List[str]
    ai_response: str = Field(description="The Filter Agent response")


agent = Agent(
    model="gemini-1.5-flash",
    deps_type=GeminiDependencies,
    name="Filter Agent",
    result_type=FilterSchema,
    system_prompt=filter_agent_prompt,
)

async def filter_agent(user_query: str, products: List[Dict[str, Any]], current_filters)-> List[Dict[str, Any]]:
    query = f""""
                    User Query: {user_query}
                    \n\n

                    +++++++++++++++++++++++++++++++++++++++++++++

                    Current Filters: {current_filters}

                    +++++++++++++++++++++++++++++++++++++++++++++

                    \n\n

                    Product Database: {products}
                    """
    response = await agent.run(query)
    product_ids = response.data.product_ids
    results = []
    for id in product_ids:
        for product in products:
            if product["product_id"] == id: 
                results.append(product)

    return results, response.data.ai_response
