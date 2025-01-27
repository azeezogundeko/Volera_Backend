from typing import List, Dict, Any
import asyncio

from schema import GeminiDependencies
from .prompts import replier_agent_prompt
from ..tools.google import google_search

from pydantic_ai import Agent
from pydantic import Field, BaseModel
from utils.websocket import websocket_manager


class ResponseSchema(BaseModel):
    ai_response: str = Field(description="The Agent response")


async def search_product_informaton(query: str): 
    return await google_search.search(query)

agent = Agent(
    model="gemini-1.5-flash",
    deps_type=GeminiDependencies,
    name="Response Agent",
    result_type=ResponseSchema,
    system_prompt=replier_agent_prompt,
    tools=[search_product_informaton]
)

async def response_agent(websocker_id, query, product): 
    message_history = []
    while True:

        query = f"""

        USER QUESTION: {query}

        PRODUCT IN QUESTION: {product}
        
        """

        response = await agent.run(query)
        message_history = message_history + response.new_messages()

        await websocket_manager.send_json(websocker_id,
        
        {
            "type": "PRODUCT_DETAILS_RESPONSE", 
            "aiResponse": response.data.ai_response,
        })

        websocket = websocket_manager.get_websocket(websocker_id)

        response = await asyncio.wait_for(websocket.receive_json(), timeout=300.0)
        if response is None:
            break
        data = response["data"]
        query = data["query"]
        product = data["product"]
    