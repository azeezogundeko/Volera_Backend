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
from agents.tools.google import GoogleSearchTool

# Initialize shared instances
google_search = GoogleSearchTool()
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
    
    
    # Create a cache key that includes both query and site
    cache_key = f"{query}_{site}"
    product_id = ecommerce_manager.generate_product_id(cache_key)
    cache_results = None
    
    # Check cache first using the combined cache key
    if not bypass_cache:
        try:
            cache_results = await ecommerce_manager.store.query(query)
            
        except Exception as e:
            logger.error(e, exc_info=True)

        if cache_results is not None:
            logger.info(f"Cache hit for query: {query}")
            results = await reranker.rerank(query, cache_results, len(cache_results))

            # For site-specific cache, verify the source matches
            if site != "all":
                results = [p for p in results if ecommerce_manager._integrations[p.get("source", "")].matches_url(site)]
            
            return post_process_results(page, limit, results, sort, filters)

    all_products = []
    
    # Get all available integrations
    integrations = ecommerce_manager._integrations.values()
    
    # Filter integrations based on site parameter
    if site and site != "all":
        # Filter for specific site
        integrations = [i for i in integrations if i.matches_url(site)]
        if not integrations:
            print(f"No supported integration found for site: {site}")
            return []
    
    # Group integrations by type
    direct_integrations = [i for i in integrations if i.integration_type in ["api", "graphql"]]
    scraping_integrations = [i for i in integrations if i.integration_type == "scraping"]

    # Handle direct API/GraphQL integrations
    for integration in direct_integrations:
        try:
            results = await integration.get_product_list(
                url="",  # Empty URL since we're using direct API
                search=query,
                page=page-1,  # Convert to 0-based index
                limit=limit,
                sort=sort
            )
            if isinstance(results, dict) and "products" in results:
                products = results["products"]
                for product in products:
                    product["source"] = integration.name
                all_products.extend(products)
            elif isinstance(results, list):
                for product in results:
                    product["source"] = integration.name
                all_products.extend(results)
        except Exception as e:
            print(f"Error with {integration.name}: {str(e)}")

    # Handle scraping-based integrations
    if scraping_integrations:
        # Search each scraping site separately to ensure all sites are covered
        all_search_results = []
        for integration in scraping_integrations:
            try:
                site_patterns = integration.url_patterns
                site_results = await google_search.search_shopping(query, site="|".join(site_patterns))
                if site_results:
                    all_search_results.extend(site_results)
            except Exception as e:
                logger.info(f"Error searching {integration.name}: {str(e)}")
        
        if all_search_results:
            # Distribute max_results across all sites
            results_per_site = max(1, max_results // len(scraping_integrations))
            urls = []
            for integration in scraping_integrations:
                # Filter URLs for this integration
                integration_urls = [
                    result["link"] for result in all_search_results 
                    if integration.matches_url(result["link"])
                ][:results_per_site]
                urls.extend(integration_urls)
            
            tasks = [
                ecommerce_manager.process_url(
                    url=url,
                    bypass_cache=bypass_cache,
                    ttl=3600
                ) for url in urls
            ]
            results = await asyncio.gather(*tasks)
            
            for result in results:
                if isinstance(result, dict):
                    products = result.get("products", [])
                    if products:
                        all_products.extend(products)
                elif isinstance(result, list):
                    all_products.extend(result)

    # Filter out failed extractions and ensure all products have a source
    successful_products = [
        p for p in all_products 
        if isinstance(p, dict) and p.get("source") not in [
            "failed_extraction", 
            "unsupported_site", 
            "error"
        ]
    ]
    
    if successful_products:
        # Cache the successful results with the site-specific cache key
        results = await reranker.rerank(query, successful_products, len(results))
        # await ecommerce_manager.db_manager.set(
        #     key=product_id,
        #     value=results,
        # )
        try:
            await ecommerce_manager.store.add(product_id, query, results)
        
        except Exception as e:
            logger.error(e, exc_info=True)
        # return results
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