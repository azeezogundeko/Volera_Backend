from typing import List, Dict, Any
from datetime import datetime

from pydantic_ai import Agent
from pydantic import BaseModel, Field

from .schema import ProductResponse
from ..auth.model import UserPreferences
from .prompt import PRODUCT_DETAIL_EXTRACTOR_SYSTEM_PROMPT, SYSTEM_PROMPT, VALIDATOR_SYSTEM_PROMPT

from agents.tools.list_operations import ListTools, ProductDetail, Specification
from agents.tools.search import search_tool
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from schema import GeminiDependencies
from crawl4ai import CrawlerRunConfig

from utils.rerank import ReRanker
from utils._craw4ai import CrawlerManager
from utils.url_shortener import URLShortener
from utils.logging import logger

shortener = URLShortener()
reranker = ReRanker()


class ResultSchema(BaseModel):
    comment: str = Field(default="", description="A comment on the result of the search")
    status: str = Field(default="success", description="The status of the search")
    no_of_items: int = Field(default=0, description="The number of items found")
    list_name: str = Field(default="", description="The name of the list")

    # products: List[ProductDetail] = Field(default_factory=list)

class Validator(BaseModel):
    is_enough: bool = Field(default=False)
    corresponding_products_ids: List[str] = Field(default_factory=list)

async def google_search_tool(query: str): 
    logger.info(f"Searching for {query}")
    return await search_tool.search(query)

# Initialize list_tools as None, it will be set during startup
list_tools = None

async def initialize_list_tools():
    global list_tools
    list_tools = await ListTools.create()

# Create a single instance of the deep search agent
_deep_search_agent = None

def get_deep_search_agent():
    """Get or create the deep search agent instance"""
    global _deep_search_agent
    if _deep_search_agent is None and list_tools is not None:
        _deep_search_agent = Agent(
            model="gemini-2.0-flash-exp",
            deps_type=GeminiDependencies,
            name="Deep Search Agent",
            result_type=ResultSchema,
            system_prompt=SYSTEM_PROMPT,
            tools=[
                google_search_tool,
                get_web_page_contents,
                list_tools.save_to_list,
                list_tools.get_from_list,
                list_tools.remove_from_list,
                list_tools.count_items,
                product_detail_extractor_agent
            ]
        )
    return _deep_search_agent

# Create a single instance of the validator agent
_validator_agent = None

def get_validator_agent():
    """Get or create the validator agent instance"""
    global _validator_agent
    if _validator_agent is None:
        _validator_agent = Agent(
            model="gemini-1.5-flash",
            deps_type=GeminiDependencies,
            result_type=Validator,
            system_prompt=VALIDATOR_SYSTEM_PROMPT,
            name="Deep Search Product Validator",
            tools=[]  # Validator doesn't need tools
        )
    return _validator_agent


async def product_detail_extractor_agent(content: str):
    agent = Agent(
        model="gemini-1.5-flash",
        deps_type=GeminiDependencies,
        name="Product Detail Extractor Agent",
        result_type=ProductDetail,
        system_prompt=PRODUCT_DETAIL_EXTRACTOR_SYSTEM_PROMPT,
    )
    logger.info(f"Extracting product details from {content}")
    response = await agent.run(content)
    return response.data

async def get_web_page_contents(urls: List[str]):
    # Configure the markdown generator with optimized settings
    logger.info(f"Getting web page contents for {urls}")
    markdown_generator = DefaultMarkdownGenerator(
        options={
            "ignore_links": False,  # Keep links for product references
            "escape_html": True,    # Clean HTML entities
            "body_width": 120,      # Wider text for better readability
            "include_sup_sub": True # Better handling of special text
        }
    )

    config = CrawlerRunConfig(
        markdown_generator=markdown_generator,
        magic=True
    )

    crawler = await CrawlerManager.get_crawler()
    # Apply the crawler with markdown generation
    responses = await crawler.arun_many(
        urls=urls,
        exclude_external_links=False,
        config=config
    )

    # Process each response and extract content
    contents = []
    for response in responses:
        if not response.success or not response.html:
            continue
        contents.append(response.markdown)

    logger.info(f"Contents: {contents}")
    return contents


async def get_user_preferences(user_id: str):
    try:
        response = await UserPreferences.read(user_id)
        return response.to_dict()
    except Exception:
        return {}


async def run_deep_search_agent(user_id: str, query: str, n_k: int, products: List[ProductResponse]) -> List[ProductDetail]:
    """
    Run the deep search agent to find relevant products.
    
    Args:
        user_id: The ID of the user making the request
        query: The search query
        n_k: Number of results to return
        products: List of existing products to exclude from search
        
    Returns:
        List of ProductDetail objects
    """
    validator_agent = get_validator_agent()
    deep_search_agent = get_deep_search_agent()
    
    if not deep_search_agent or not validator_agent:
        raise RuntimeError("Agents not properly initialized. Make sure list_tools is initialized first.")

    query_with_products = f"User Query {query}, \n Products {products}"
    results = await validator_agent.run(query_with_products)
    logger.info(f"Validator results: {results}")

    response = results.data
    if response.is_enough:
        return products

    products = [product for product in products if product["product_id"] in response.corresponding_products_ids]
    logger.info(f"Products: {products}")

    list_name = f"deep_search_{user_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    
    # Convert dictionaries to ProductDetail instances
    try:
        product_details = []
        for product in products:
            # Clean the dictionary to remove None values and ensure all required fields
            cleaned_data = {k: v for k, v in product.items() if v is not None}
            # Convert specifications if they exist
            if 'specifications' in cleaned_data:
                cleaned_data['specifications'] = [
                    Specification(**spec) if isinstance(spec, dict) else spec 
                    for spec in cleaned_data['specifications']
                ]
            # Create ProductDetail instance
            product_detail = ProductDetail(**cleaned_data)
            product_details.append(product_detail)
            
        logger.info(f"Created {len(product_details)} ProductDetail instances")
    except Exception as e:
        logger.error(f"Error creating ProductDetail instances: {str(e)}")
        raise Exception(f"Failed to create ProductDetail instances: {str(e)}")
    
    # Save to list and check result
    save_result = list_tools.save_to_list(list_name, product_details)
    if not save_result['success']:
        logger.error(f"Failed to save to list: {save_result['message']}")
        raise Exception(f"Failed to save to list: {save_result['message']}")
        
    user_preferences = await get_user_preferences(user_id)
    user_prompt = (
        f"List Name: {list_name} \n"
        f"User Query: {query} \n"
        f"Number of Results Wanted: {n_k} \n"
        f"Already Matched Products: {products} \n"
        f"User Preferences: \n{user_preferences}"
    )
    
    products = await deep_search_agent.run(user_prompt)
    logger.info(f"Deep search results: {products}")
    
    # Get from list and check result
    get_result = list_tools.get_from_list(list_name)
    if not get_result['success']:
        logger.error(f"Failed to get from list: {get_result['message']}")
        raise Exception(f"Failed to get from list: {get_result['message']}")
        
    products = get_result['data']
    print(products)
    if not products:
        logger.warning("No products found in list")
        raise Exception("No products found in list")

    ps = []
    for product in products:
        # Create a new model instance with updated product_id
        updated_product = product.model_copy(update={
            'product_id': shortener.shorten_url(product.url)
        })
        ps.append(updated_product.model_dump())

    return ps
    # reranked_products = await reranker.rerank(query, ps)
    # return reranked_products


