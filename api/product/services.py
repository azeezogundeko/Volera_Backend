import asyncio
from typing import List, Dict, Any, Optional
from datetime import timedelta

from utils.ecommerce_manager import EcommerceManager
from agents.tools.google import GoogleSearchTool

# Initialize shared instances
ecommerce_manager = EcommerceManager(cache_duration=timedelta(hours=24))
google_search = GoogleSearchTool()

async def list_products(
    query: str,
    site: Optional[str] = None,
    max_results: int = 5,
    bypass_cache: bool = False,
    page: int = 1,
    limit: int = 40,
    sort: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get product listings from supported e-commerce sites."""
    
    # Check cache first using the query as cache key
    if not bypass_cache:
        cached_data = ecommerce_manager.get_cached_data(query=query, type="list")
        if cached_data:
            return cached_data

    all_products = []
    
    # Get all available integrations
    integrations = ecommerce_manager._integrations.values()
    
    # Filter integrations based on site parameter
    if site and site != "all":
        integrations = [i for i in integrations if any(pattern in site for pattern in i.url_patterns)]
    
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
                all_products.extend(results["products"])
            elif isinstance(results, list):
                all_products.extend(results)
        except Exception as e:
            print(f"Error with {integration.name}: {str(e)}")

    # Handle scraping-based integrations
    if scraping_integrations:
        scraping_sites = [pattern for i in scraping_integrations for pattern in i.url_patterns]
        search_results = await google_search.search_shopping(query, site=",".join(scraping_sites))
        if search_results:
            urls = [p["link"] for p in search_results[:max_results]]
            tasks = [
                ecommerce_manager.process_url(
                    url=url,
                    bypass_cache=bypass_cache,
                    ttl=3600
                ) for url in urls
            ]
            results = await asyncio.gather(*tasks)

            print(results)
            
            for result in results:
                if isinstance(result, dict):
                    products = result.get("products", [])
                    if products:
                        all_products.extend(products)
                elif isinstance(result, list):
                    all_products.extend(result)

    # Filter out failed extractions
    successful_products = [
        p for p in all_products 
        if isinstance(p, dict) and p.get("source") not in [
            "failed_extraction", 
            "unsupported_site", 
            "error"
        ]
    ]
    
    if successful_products:
        # Cache the successful results
        ecommerce_manager.cache_data(query, type="list", data=successful_products, ttl=3600)
        return successful_products
    
    return []

async def get_product_detail(
    product_url: str,
    bypass_cache: bool = False,
    ttl: Optional[int] = 3600
) -> Dict[str, Any]:
    """Get detailed product information from a specific URL."""
    product = await ecommerce_manager.get_product_detail(
        product_url=product_url,
        bypass_cache=bypass_cache,
        ttl=ttl
    )
    return product

def get_cache_info(url: str) -> Optional[Dict[str, Any]]:
    """Get cache information for a specific URL."""
    return ecommerce_manager.get_cache_info(url)

def clear_cache() -> None:
    """Clear all cached data."""
    ecommerce_manager.clear_cache()

def remove_expired_cache() -> None:
    """Remove all expired cache entries."""
    ecommerce_manager.remove_expired_cache()

def set_cache_ttl(url: str, ttl: int) -> bool:
    """Set TTL for a specific cached URL."""
    return ecommerce_manager.set_ttl(url, ttl)