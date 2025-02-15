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
from agents.tools.search import search_tool

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
    query: str,
    site: Optional[str] = "all",
    max_results: int = 5,
    bypass_cache: bool = False,
    page: int = 1,
    limit: int = 40,
    sort: Optional[Dict[str, Any]] = None,
    filters: dict = None
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
                    results = [p for p in results if ecommerce_manager._integrations[p.get("source", "")].matches_url(site)]
                return post_process_results(page, limit, results, sort, filters)
        except Exception as e:
            logger.error(e, exc_info=True)

    integrations = ecommerce_manager._integrations.values()
    if site and site != "all":
        integrations = [i for i in integrations if i.matches_url(site)]
        if not integrations:
            logger.info(f"No supported integration found for site: {site}")
            return []

    # Prepare integrations
    direct_integrations = [i for i in integrations if i.integration_type in ["api", "graphql"]]
    scraping_integrations = [i for i in integrations if i.integration_type == "scraping"]
    all_products = []

    # Parallel processing for direct integrations
    if direct_integrations:
        direct_tasks = [
            integration.get_product_list(
                url="",
                search=query,
                page=page-1,
                limit=limit,
                sort=sort
            ) for integration in direct_integrations
        ]
        direct_results = await asyncio.gather(*direct_tasks, return_exceptions=True)
        
        for integration, result in zip(direct_integrations, direct_results):
            if isinstance(result, Exception):
                logger.error(f"Error with {integration.name}: {str(result)}")
                continue
            products = []
            if isinstance(result, dict):
                products = result.get("products", [])
            elif isinstance(result, list):
                products = result
            for p in products:
                p["source"] = integration.name
            all_products.extend(products)

    # Parallel processing for scraping integrations
    if scraping_integrations:
        # Parallel search across all scraping sites
        search_tasks = [
            search_tool.search_products(query, site="|".join(integration.url_patterns))
            for integration in scraping_integrations
        ]
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process search results
        all_search_results = []
        for integration, result in zip(scraping_integrations, search_results):
            if isinstance(result, Exception):
                logger.error(f"Search error {integration.name}: {str(result)}")
                continue
            if result:
                all_search_results.extend(result)

        # Process product URLs in parallel
        if all_search_results:
            results_per_site = max(1, max_results // len(scraping_integrations))
            url_tasks = []
            url_integration_map = {}
            
            # Map URLs to their integrations
            for result in all_search_results:
                for integration in scraping_integrations:
                    if integration.matches_url(result["link"]):
                        if url_integration_map.get(integration.name, 0) < results_per_site:
                            url_tasks.append(
                                ecommerce_manager.process_url(
                                    url=result["link"],
                                    bypass_cache=bypass_cache,
                                    ttl=3600
                                )
                            )
                            url_integration_map[integration.name] = url_integration_map.get(integration.name, 0) + 1
                        break

            # Process URLs in parallel
            if url_tasks:
                url_results = await asyncio.gather(*url_tasks)
                for result in url_results:
                    if isinstance(result, dict):
                        products = result.get("products", [])
                        all_products.extend(products)
                    elif isinstance(result, list):
                        all_products.extend(result)

    # Filter and process results
    excluded_sources = {"failed_extraction", "unsupported_site", "error"}
    successful_products = [
        p for p in all_products
        if isinstance(p, dict) and p.get("source") not in excluded_sources
    ]

    if successful_products:
        results = await reranker.rerank(query, successful_products)
        try:
            await ecommerce_manager.store.add(product_id, query, results)
        except Exception as e:
            logger.error(e, exc_info=True)
        return post_process_results(page, limit, results, sort, filters)

    return []


def post_process_results(
    page,
    limit,
    results: List[Dict[str, Any]], 
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
    
    return results[:limit]


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