import asyncio
from typing import List, Dict, Any, Optional
from datetime import timedelta
from fastapi import Request

from utils.ecommerce_manager import EcommerceManager
from utils.rerank import ReRanker
from agents.tools.google import GoogleSearchTool

# Initialize shared instances
google_search = GoogleSearchTool()
reranker = ReRanker()

def get_ecommerce_manager(request: Request) -> EcommerceManager:
    """Get EcommerceManager instance from request state."""
    return EcommerceManager(
        db_manager=request.state.db_manager,
        similarity_threshold=0.8
    )

async def list_products(
    request: Request,
    query: str,
    site: Optional[str] = "all",
    max_results: int = 5,
    bypass_cache: bool = False,
    page: int = 1,
    limit: int = 40,
    sort: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get product listings from supported e-commerce sites."""
    
    ecommerce_manager = get_ecommerce_manager(request)
    
    # Create a cache key that includes both query and site
    cache_key = f"{query}_{site}"
    product_id = ecommerce_manager.generate_product_id(cache_key)
    
    # Check cache first using the combined cache key
    if not bypass_cache:
        cached_data = await ecommerce_manager.db_manager.get_cached_product(
            product_id=product_id,
        )
        if cached_data:
            # For site-specific cache, verify the source matches
            if site != "all":
                cached_data = [p for p in cached_data if ecommerce_manager._integrations[p.get("source", "")].matches_url(site)]
            return cached_data

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
                print(f"Error searching {integration.name}: {str(e)}")
        
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
        results = await reranker.rerank(query, successful_products, limit)
        await ecommerce_manager.db_manager.cache_product(
            product_id=product_id,
            data=results,
            ttl=3600,
            query=cache_key
        )
        return results
    
    return []

async def get_product_detail(
    request: Request,
    product_id: str,
    bypass_cache: bool = False,
    ttl: Optional[int] = 3600
) -> Dict[str, Any]:
    """Get detailed product information from a specific URL."""
    ecommerce_manager = get_ecommerce_manager(request)
    product = await ecommerce_manager.get_product_detail(
        product_id=product_id,
        bypass_cache=bypass_cache,
        ttl=ttl
    )
    return product

async def get_cache_info(request: Request, url: str) -> Optional[Dict[str, Any]]:
    """Get cache information for a specific URL."""
    ecommerce_manager = get_ecommerce_manager(request)
    product_id = ecommerce_manager.generate_product_id(url)
    return await ecommerce_manager.db_manager.get_cache_stats()

async def clear_cache(request: Request) -> None:
    """Clear all cached data."""
    ecommerce_manager = get_ecommerce_manager(request)
    await ecommerce_manager.db_manager.clear_cache()

async def remove_expired_cache(request: Request) -> None:
    """Remove all expired cache entries."""
    ecommerce_manager = get_ecommerce_manager(request)
    await ecommerce_manager.db_manager.remove_expired_cache()

async def set_cache_ttl(request: Request, url: str, ttl: int) -> bool:
    """Set TTL for a specific cached URL."""
    ecommerce_manager = get_ecommerce_manager(request)
    product_id = ecommerce_manager.generate_product_id(url)
    # Re-cache the product with new TTL
    cached_product = await ecommerce_manager.db_manager.get_cached_product(product_id)
    if cached_product:
        await ecommerce_manager.db_manager.cache_product(
            product_id=product_id,
            data=cached_product,
            ttl=ttl
        )
        return True
    return False