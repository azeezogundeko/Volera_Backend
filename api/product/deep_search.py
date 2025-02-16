from typing import List, Dict, Any
from datetime import datetime

from pydantic_ai import Agent
from pydantic import BaseModel, Field

from .schema import ProductResponse
from ..auth.model import UserPreferences

from agents.tools.list_operations import ListTools
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

class Specification(BaseModel):
    label: str 
    value: str 

class ProductDetail(BaseModel):
    product_id: str = ''
    name: str = ''
    brand: str = ''
    category: str = ''
    currency: str = '₦'
    description: str = ''
    current_price: float = 0.0
    original_price: float  = 0.0
    discount: float = 0.0
    url: str = ''
    image: str = ''
    source: str = Field(None, description='The source of the product eg Amazon, Jumia, Konga, etc')
    rating: float = 0.0
    rating_count: int  = 0
    specifications: List[Specification] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)

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
                list_tools.count_items
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


SYSTEM_PROMPT = """
Product Search Workflow Manager

This system manages product searches by orchestrating lists and ensuring results match user specifications. The agent receives a prompt that includes:

- List Name: A unique identifier for the current product list.
- User Query: The search terms provided by the user.
- Number of Results Wanted: The total quantity of matching products desired.
- Already Matched Products: A record of products already found.
- User Preferences: Additional details or constraints specified by the user.

Core Process:

1. List Creation:
   - Generate a unique list name based on a timestamp and a hash of the query.
   - Verify that the list is properly initialized.

2. Search Execution:
   - Perform targeted searches on Nigerian e-commerce sites (e.g., Jumia, Konga) using the user query.
   - Extract and process URLs from the search results.
   - Retrieve web page content and parse out product details according to a predefined schema.

3. Product Validation and Saving:
   - Validate that each product has required fields: name, current_price, URL, and source.
   - Ensure the product price is within the user's budget and not zero.
   - Confirm that the product URL is from a Nigerian domain.
   - Save validated products to the list while avoiding duplicates.

4. Completion Check:
   - Continuously monitor the number of products in the list.
   - Stop searching once the number of validated products reaches the target count.

5. Final Output:
   - Return only the result schema once the target number of products is achieved.
   - Do not expose any internal product data.

Error Handling:
   - If the list expires (TTL reached), create a new list with a retry suffix and resume from the last successful point.
   - Remove any products that fail validation from the list.

Summary:
The agent's task is to identify and add the remaining products needed to meet the user's specified quantity while ensuring compliance with internal validation rules and user requirements. Once the target is met, only the list name is returned.
"""


VALIDATOR_SYSTEM_PROMPT = """You are a precise product validator. Your role is to analyze product search results and determine if they truly match the user's search query.

For each product, carefully evaluate if it genuinely corresponds to what the user is looking for, considering:
- Product description
- Product features
- Product categories
- Product specifications

Your task is to:
1. Analyze if ALL products in the results match the user's query
2. If not all products match, identify only the product IDs that are truly relevant

Output requirements:
- Set is_enough to true only if ALL products match the query with the no equal to the one the user is looking for
- If is_enough is false, provide corresponding_products_ids containing only the IDs of matching products
- If no products match, return an empty list for corresponding_products_ids

Be strict in your validation - only include products that genuinely match the user's search intent."""

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
    print(products)
    
    # Get from list and check result
    get_result = list_tools.get_from_list(list_name)
    if not get_result['success']:
        logger.error(f"Failed to get from list: {get_result['message']}")
        raise Exception(f"Failed to get from list: {get_result['message']}")
        
    products = get_result['data']
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


