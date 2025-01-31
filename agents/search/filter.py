from typing import List, Dict, Any

from schema import GeminiDependencies
from .prompts import filter_agent_prompt
from api.track.scrape import scraper
from ..legacy.llm import track_llm_call, check_credits
from ..tools.google import google_search
from utils.websocket import websocket_manager

from pydantic_ai import Agent
from pydantic import Field, BaseModel


class FilterSchema(BaseModel):
    product_ids: List[str]
    ai_response: str = Field(description="The Filter Agent response")


async def get_product_details(product_id: str):
    return await scraper.get_product_details(product_id)

async def search_product_informaton(query: str): 
    return await google_search.search(query)

agent = Agent(
    model="gemini-1.5-flash",
    deps_type=GeminiDependencies,
    name="Filter Agent",
    result_type=FilterSchema,
    system_prompt=filter_agent_prompt,
    tools=[get_product_details, search_product_informaton]
)


async def filter_agent(websocket_id, user_query: str, user_id, products: List[Dict[str, Any]], current_filters)-> List[Dict[str, Any]]:
    query = f""""
                    User Query: {user_query}
                    \n\n
                    +++++++++++++++++++++++++++++++++++++++++++++
                    Current Filters: {current_filters}
                    +++++++++++++++++++++++++++++++++++++++++++++
                    \n\n
                    Product Database: {products}
                """

    has_credits, credits =  await check_credits(user_id, "text")
    if has_credits is False:
        await websocket_manager.send_json(
            websocket_id, {
                "type": "ERROR",
                "message": "Oops! It looks like you've run out of credits. Please purchase more credits to continue using my assistance. 😊"
            }
        )

        return

    response = await agent.run(query)
    await track_llm_call(user_id, "text")

    product_ids = response.data.product_ids
    results = []
    for id in product_ids:
        for product in products:
            if product["product_id"] == id: 
                results.append(product)

    # return results, response.data.ai_response

    await websocket_manager.send_json(
            websocket_id,
            {
            "type": "FILTER_RESPONSE",
            "data": {
            "filters": results,
            "aiResponse": response.data.ai_response
            }}
        )
