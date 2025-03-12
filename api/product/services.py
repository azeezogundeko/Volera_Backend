import asyncio
import difflib
from typing import List, Dict, Any, Optional
# from datetime import timedelta
from fastapi import Request


from .model import Product, WishList
from .schema import ProductDetail
from ..auth.schema import UserIn
from utils.ecommerce_manager import EcommerceManager
from utils.rerank import ReRanker
from utils.logging import logger
from utils.product_utils import search_and_process_products
# from .deep_search import run_deep_search_agent

# Initialize shared instances
# google_search = GoogleSearchTool()
reranker = ReRanker()

def get_ecommerce_manager(request: Request) -> EcommerceManager:
    """Get EcommerceManager instance from request state."""
    return EcommerceManager(
        db_manager=request.state.db_cache,
        similarity_threshold=0.8
    )


def is_string_match(str1: str, str2: str, threshold=0.5):
    # Convert both strings to lowercase for case-insensitive comparison
    str1_lower = str1.lower()
    str2_lower = str2.lower()
    
    # Calculate similarity ratio using SequenceMatcher
    matcher = difflib.SequenceMatcher(None, str1_lower, str2_lower)
    similarity_ratio = matcher.ratio()
    
    # Check if the ratio meets or exceeds the threshold
    return similarity_ratio >= threshold


def sort_products(products: List[dict], sort_key: str, reverse=False) -> List[dict]:
    """Sort the list of products based on the given key."""

    if sort_key == 'lowest price':
        return sorted(products, key=lambda x: x.get('current_price', float('inf')), reverse=False)
    elif sort_key == 'highest price':
        return sorted(products, key=lambda x: x.get('current_price', float('-inf')), reverse=True)
    elif sort_key in ['highest ratings', 'best rated']:
        return sorted(products, key=lambda x: x.get('rating', float('inf')), reverse=True)
    elif sort_key == 'most relevant':
        # products are already reranked
        return products
    elif sort_key == 'price':
        return sorted(products, key=lambda x: x.get('current_price', float('inf')), reverse=reverse)
    elif sort_key == 'ratings':
        return sorted(products, key=lambda x: x.get('rating', float('inf')), reverse=reverse)
    return products  # Default return if no valid sort_key is provided.


def filter_products(products: List[dict], filters: Dict[str, str]) -> List[dict]:
    """
    Filter the list of products based on the given filters.
    Supported filters: 'brand', 'category', 'price'.
    """
    # Ensure filters is not empty
    if not filters:
        return products

    # Combine brand and category into a product name filter, if present
    prod_name = None
    if filters.get("brand") and filters.get("category"):
        prod_name = f"{filters['brand']} {filters['category']}"

    try:
        # Filter by name match (brand + category)
        # if prod_name:
        #     products = [p for p in products if is_string_match(prod_name, p.get("name", ""))]

        # Iterate over filters for additional filtering
        for key, value in filters.items():
            if key == "price":  # Price filter
                products = [p for p in products if "current_price" in p and value >= p["current_price"]]
            # elif key not in ("brand", "category"):  # Future support for additional keys
            #     products = [p for p in products if key in p and p[key] == value]

    except Exception as e:
        # Log or handle the exception as needed
        print(f"Error during filtering: {e}")

    return products


async def list_products(
    ecommerce_manager: EcommerceManager,
    user_id: str,
    query: str,
    site: Optional[str] = "all",
    max_results: int = 5,
    bypass_cache: bool = False,
    page: int = 1,
    limit: int = 40,
    sort: Optional[Dict[str, Any]] = None,
    filters: dict = None,
    deep_search: bool = False
) -> List[Dict[str, Any]]:
    """Get product listings from supported e-commerce sites."""
    
    cache_key = f"{query}_{site}"
    product_id = ecommerce_manager.generate_product_id(cache_key)
    
    # Cache check
    if not bypass_cache:
        try:
            cache_results = await ecommerce_manager.store.query(query)
            if cache_results is not None:
                logger.info(f"Cache hit for query: {query}")
                results = await reranker.rerank(query, cache_results)
                if site != "all":
                    results = [p for p in results if ecommerce_manager._integrations[p.get("source".lower(), "")].matches_url(site)]
                if len(results) > 0:  # Only return cached results if we found matches
                    return await post_process_results(user_id, query, page, limit, deep_search, results, sort, filters)
                else:
                    logger.info(f"Cache hit but no matching results for query: {query}. Fetching fresh results.")
        except Exception as e:
            logger.error(e, exc_info=True)

    # Get fresh results using the shared utility function   
    logger.info(f"Fetching fresh results for query: {query}")
    results = await search_and_process_products(
        ecommerce_manager,
        query=query,
        max_results=max_results,
        site=site,
        limit=limit,
        bypass_cache=bypass_cache
    )

    if results:
        try:
            await ecommerce_manager.store.add(product_id, query, results)
            logger.info(f"Cached {len(results)} new results for query: {query}")
        except Exception as e:
            logger.error(f"Error caching results: {e}", exc_info=True)
            
        return await post_process_results(user_id, query, page, limit, deep_search, results, sort, filters)
    else:
        logger.info(f"No results found for query: {query}")

    return []


async def post_process_results(
    user_id: str,
    query: str, 
    page,
    limit,
    deep_search=False,
    results: List[Dict[str, Any]] = [], 
    sort: Optional[str] = None,
    filters: dict = None) -> List[Dict[str, Any]]:
        
    # # Apply pagination
    # start_index = (page - 1) * limit
    # end_index = start_index + limit
    # results = results[start_index:end_index] 
            
    if filters:
        # Check if any filter value is not None
        filters = {key: value for key, value in filters.items() if value is not None}
    
        # Check if there are remaining filters
        if filters:
            re = filter_products(results, filters)
            if len(re) > 0:
                results = re

    if sort:
        results = sort_products(results, sort)
    
    results = results[:limit]

    if deep_search:
        pass
        # try:
        #     results = await run_deep_search_agent(user_id, query, limit, results)
        # except Exception as e:
        #     logger.error(e, exc_info=True)

    return results


async def get_product_detail(
    ecommerce_manager: EcommerceManager,
    product_id: str,
    bypass_cache: bool = False,
    ttl: Optional[int] = 3600
) -> Dict[str, Any]:
    """Get detailed product information from a specific URL."""
    product = await ecommerce_manager.get_product_detail(
        product_id=product_id,
        bypass_cache=bypass_cache,
        ttl=ttl
    )
    return product


async def save_product(product: ProductDetail, user: UserIn):
    """Save a product to the user's saved products."""
    specifications = [str(
        dict(label=spec.label, value=spec.value)
    ) for spec in product.specifications]

    product = await Product.get_or_create( 
        product.product_id, 
        dict(
        currency=product.currency,
        name=product.name,
        url=product.url,
        current_price=product.current_price,
        image=product.image,
        features=product.features,
        specification=specifications,
        ratings=product.rating,
        source=product.source,
        original_price=product.original_price,
        brand=product.brand,
        discount=product.discount,
        reviews_count=product.rating_count)
        )

    # if is_wishlist:

    wishlist = await WishList.create(
        WishList.get_unique_id(),
        {"user_id": user.id, "product_id": product.id}
    )

    results = {
        "product": product.to_dict(),
        "wishlist": wishlist.to_dict()
    }

    return {
        "message": "success",
        "data": results,
        "error": None
    }


async def get_trending_products(
    ecommerce_manager: EcommerceManager,
    page: int = 1,
    limit: int = 50,
    max_results: int = 3
) -> List[Dict[str, Any]]:
    """
    Get trending products without requiring a search query.
    Uses predefined categories and sorting to determine trending items.
    """
    try:
        # Get products from popular categories
        categories = ["electronics", "fashion", "home", "beauty"]
        all_products = []
        
        for category in categories:
            products = await list_products(
                ecommerce_manager=ecommerce_manager,
                user_id="system",  # System-level request
                query=category,    # Use category as query
                max_results=max_results,
                page=1,           # Get first page for each category
                limit=limit,
                sort={"key": "highest ratings"},  # Sort by ratings to get popular items
                deep_search=False  # No need for deep search
            )
            all_products.extend(products)
        
        # Sort by rating and recent additions
        trending = sorted(
            all_products,
            key=lambda x: (x.get('rating', 0), x.get('timestamp', '')),
            reverse=True
        )
        
        # Apply pagination to final results
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        return trending[start_idx:end_idx]
        
    except Exception as e:
        logger.error(f"Error getting trending products: {e}")
        return []