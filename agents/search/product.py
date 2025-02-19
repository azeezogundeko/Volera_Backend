import asyncio
from typing import List, Dict, Any

from schema import GeminiDependencies
from .prompts import product_agent_prompt

from ..legacy.llm import check_credits, track_llm_call
from ..tools.search import search_tool
from ..tools.general import (
    track_product_price,
    get_product_specifications,
    get_user_preferences,
    save_product_to_waishlist,
    search_product_list
)

from pydantic_ai import Agent
from pydantic import Field, BaseModel
from utils.websocket import websocket_manager

class Specification(BaseModel):
    label: str 
    value: str 

class ProductDetail(BaseModel):
    product_id: str
    name: str = ''
    brand: str = ''
    category: str = ''
    currency: float = '₦'
    description: str = ''
    current_price: str = 0.0
    original_price: float  = 0.0
    discount: float = 0.0
    url: str = ''
    image: str = ''
    source: str = Field(None)
    rating: float = 0.0
    rating_count: int  = 0
    specifications: List[Specification] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    

class ResponseSchema(BaseModel):
    ai_response: str = Field(description="The Agent response")
    # action: str = Field(description="The action to be implemented")
    product_ids: List[str] = Field([], description="The list of product id")
    searched_products: List[ProductDetail] = []


async def normal_google_search(query: str): 
    return await search_tool.search(query)


    

agent = Agent(
    model="gemini-1.5-flash",
    deps_type=GeminiDependencies,
    name="Product Agent",
    result_type=ResponseSchema,
    system_prompt=product_agent_prompt,
    tools=[
        normal_google_search,
        # save_product_to_waishlist,
        search_product_list,
        # get_product_specifications,
        # track_product_price
        ]
)

async def product_agent(websocker_id,user_id, query, products, message_history): 
    # message_history = []
    user_preferences = await get_user_preferences(user_id)
    query = f"USER_PREFERENCES: {user_preferences} \n USER QUESTION: {query} \n PRODUCTS IN QUESTION: {products}"
    # while True:
    

    has_credits, credits =  await check_credits(user_id, "text")
    if has_credits is False:
        await websocket_manager.send_json(websocker_id,
    
        data={
            "type": "ERROR", 
            "message": "Oops! It looks like you've run out of credits. Please purchase more credits to continue using my assistance. 😊",
            # "response": "Oops! It looks like you've run out of credits. Please purchase more credits to continue using my assistance. 😊"
        })
        
        return message_history


    response = await agent.run(query, message_history=message_history)

    message_history = message_history + response.new_messages()
    await track_llm_call(user_id, type= 'amount', amount=20)

    result = preprocess_results(response.data, products)
    await websocket_manager.send_json(websocker_id,
    {
        "type": "AGENT_RESPONSE",
        "action": result["action"],
        "data": {
            "searchResults":  result["searchResults"],
            "filters": result["filters"],
            "aiResponse": result["response"]
        }}
    )
    return message_history
    # websocket = websocket_manager.get_websocket(websocker_id)

    # response = await asyncio.wait_for(websocket.receive_json(), timeout=300.0)
    # if response is None:
    #     break
    # type = response["type"]
    # if type != "AGENT_REQUEST":
    #     break
    # data = response["data"]
    # query = data["message"]
    # query = f"USER_ID: {user_id} \n USER QUESTION: {query}"
        # products = data["currentProducts"]

def preprocess_results(product: ResponseSchema, products: List[Dict[str, Any]]):
    r = {}
    r["response"] = product.ai_response
    r["action"] = "RESPONSE"
    r["filters"] = []
    r["searchResults"] = []

    if product.searched_products:
        r["action"] = "SEARCH"
        r["searchResults"] = product.searched_products.__dict__

    elif product.product_ids:
        r["action"] = "FILTER"
        r["filters"] = get_product_results(product.product_ids, products)

    print(r)
    return r

    


def get_product_results(product_ids, products):
    results = []
    if products:
        for id in product_ids:
            for product in products:
                if product["product_id"] == id: 
                    results.append(product)

    return results