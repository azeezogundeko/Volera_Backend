import asyncio
from typing import Optional, Literal
from fastapi import APIRouter, HTTPException, Query
from .services import list_products, get_product_detail, get_cache_info, clear_cache, remove_expired_cache, set_cache_ttl

router = APIRouter()

@router.get("/search")
async def search_product(query: str):
    """Search for products across supported search engines."""
    products = await list_products(query=query, site=None, max_results=5)
    return products

@router.get("/shopping")
async def list_products_route(
    query: str,
    site: Optional[Literal[
        "jumia.com.ng",
        "jiji.ng",
        "konga.com",
    ]] = None,
    max_results: int = Query(default=5, ge=1, le=20),
    bypass_cache: bool = False,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=40, ge=1, le=100),
    sort: Optional[str] = None,
):
    """
    Get product listings from supported e-commerce sites.
    
    Args:
        query: Search query
        site: Specific site to search (optional)
        max_results: Maximum number of results to return per site
        bypass_cache: Whether to bypass cache
        page: Page number for pagination
        limit: Number of items per page
        sort: Sort order (site-specific)
    """
    products = await list_products(
        query=query,
        site=site,
        max_results=max_results,
        bypass_cache=bypass_cache,
        page=page,
        limit=limit,
        sort=sort
    )
    
    if not products:
        return []
    
    return products

@router.get("/product-detail")
async def get_product_detail_route(
    product_url: str,
    bypass_cache: bool = False,
    ttl: Optional[int] = 3600  # 1 hour cache
):
    """
    Get detailed product information from a specific product url.
    
    Args:
        product_url: Product URL
        bypass_cache: Whether to bypass cache
        ttl: Cache duration in seconds
    """
    product = await get_product_detail(
        product_url=product_url,
        bypass_cache=bypass_cache,
        ttl=ttl
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or failed to extract data")
    return product




















@router.get("/cache-info")
async def get_cache_info(url: str):
    """Get cache information for a specific URL."""
    info = services.get_cache_info(url)
    if not info:
        raise HTTPException(status_code=404, detail="URL not found in cache")
    return info

@router.post("/clear-cache")
async def clear_cache():
    """Clear all cached data."""
    services.clear_cache()
    return {"message": "Cache cleared successfully"}

@router.post("/remove-expired-cache")
async def remove_expired_cache():
    """Remove all expired cache entries."""
    services.remove_expired_cache()
    return {"message": "Expired cache entries removed successfully"}

@router.post("/set-ttl")
async def set_cache_ttl(url: str, ttl: int):
    """Set TTL for a specific cached URL."""
    if ttl <= 0:
        raise HTTPException(status_code=400, detail="TTL must be greater than 0")
    
    success = services.set_cache_ttl(url, ttl)
    if not success:
        raise HTTPException(status_code=404, detail="URL not found in cache")
    
    return {"message": f"TTL set to {ttl} seconds for URL"}
