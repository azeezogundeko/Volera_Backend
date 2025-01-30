import asyncio

from schema import GeminiDependencies
from .prompts import comparison_agent_prompt
from ..legacy.llm import check_credits, track_llm_call
from ..tools.google import google_search

from pydantic_ai import Agent
from pydantic import Field, BaseModel
from utils.websocket import websocket_manager


class ResponseSchema(BaseModel):
    ai_response: str = Field(description="The Agent response")


async def search_informaton(query: str): 
    return await google_search.search(query)

agent = Agent(
    model="gemini-1.5-flash",
    deps_type=GeminiDependencies,
    name="Comparison Agent",
    result_type=ResponseSchema,
    system_prompt=comparison_agent_prompt,
    tools=[search_informaton]
)

async def comparison_agent(websocker_id,user_id, query, products): 
    message_history = []
    while True:

        query = f"""

        USER QUESTION: {query}

        PRODUCTS IN QUESTION: {products}
        
        """

        has_credits =  await check_credits(user_id, "text")
        if has_credits is False:
            await websocket_manager.send_json(websocker_id,
        
            data={
                "type": "ERROR", 
                "message": "Oops! It looks like you've run out of credits. Please purchase more credits to continue using my assistance. 😊",
                # "response": "Oops! It looks like you've run out of credits. Please purchase more credits to continue using my assistance. 😊"
            })
            break


        response = await agent.run(query, message_history=message_history)
        message_history = message_history + response.new_messages()

        await websocket_manager.send_json(websocker_id,
        
        {
            "type": "COMPARE_RESPONSE", 
            "message": response.data.ai_response,
            "response": response.data.ai_response,
        })

        websocket = websocket_manager.get_websocket(websocker_id)

        response = await asyncio.wait_for(websocket.receive_json(), timeout=300.0)
        if response is None:
            break
        data = response["data"]
        query = data["query"]
        products = data["products"]
    