# import asyncio
from typing import List, Dict, Any

from schema import GeminiDependencies
from .prompts import product_agent_prompt

from ..legacy.llm import check_credits, track_llm_call
from ..tools.search import search_tool
from ..tools.general import (
    # track_product_price,
    # get_product_specifications,
    get_user_preferences,
    # save_product_to_waishlist,
    search_product_list,
    # get_ecommerce_manager
)
# from utils.product_utils import search_and_process_products

from pydantic_ai import Agent
from pydantic import Field, BaseModel
from utils.websocket import websocket_manager
from utils.logging import logger

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

async def product_agent(websocker_id, user_id, query, products, message_history): 
    from api.auth.model import UserCredits
    
    user_preferences = await get_user_preferences(user_id)
    query = f"USER_PREFERENCES: {user_preferences} \n USER QUESTION: {query} \n PRODUCTS IN QUESTION: {products}"

    # Check credits upfront
    has_credits, credits = await check_credits(user_id, "text", amount=20)
    if has_credits is False:
        await websocket_manager.send_json(websocker_id,
        data={
            "type": "ERROR", 
            "message": "Oops! It looks like you've run out of credits. Please purchase more credits to continue using my assistance. 😊",
        })
        return message_history

    try:
        # Run agent
        response = await agent.run(query, message_history=message_history)
        message_history = message_history + response.new_messages()

        # Deduct credits only after successful agent run
        await UserCredits.update_balance(
            user_id, 
            -20,
            transaction_type="product_agent_query"
        )

        # Process and send results
        result = preprocess_results(response.data, products)
        await websocket_manager.send_json(websocker_id,
        {
            "type": "AGENT_RESPONSE",
            "action": result["action"],
            "data": {
                "searchResults": result["searchResults"],
                "filters": result["filters"],
                "aiResponse": result["response"]
            }
        })
        return message_history

    except Exception as e:
        logger.error(f"Error in product agent for user {user_id}: {e}")
        await websocket_manager.send_json(websocker_id,
        {
            "type": "ERROR",
            "message": "An error occurred while processing your request. Please try again."
        })
        return message_history

def preprocess_results(product: ResponseSchema, products: List[Dict[str, Any]]):
    r = {}
    r["response"] = product.ai_response
    r["action"] = "RESPONSE"
    r["filters"] = []
    r["searchResults"] = []

    if product.searched_products:
        r["action"] = "SEARCH"
        r["searchResults"] =[product.__dict__ for product in product.searched_products]

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