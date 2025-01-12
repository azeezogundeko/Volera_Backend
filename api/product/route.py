from typing import List, Optional, Literal
from fastapi import APIRouter, Query, Request, Depends
from . import services
from .schema import ProductResponse, ProductDetail
from ..auth.schema import UserIn
from ..auth.services import get_current_user


router = APIRouter()

@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    request: Request,
    query: str = Query(..., description="Search query"),
    site: Literal["all", "jumia.com.ng", "jiji.ng", "konga.com"] = Query("all", description="Specific site to search"),
    max_results: int = Query(5, description="Maximum number of results per site"),
    bypass_cache: bool = Query(False, description="Bypass cache and fetch fresh data"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(40, description="Results per page"),
    sort: Optional[str] = Query(None, description="Sort order")
):
    """Search for products across supported e-commerce sites."""
    products = await services.list_products(
        request=request,
        query=query,
        site=site,
        max_results=max_results,
        bypass_cache=bypass_cache,
        page=page,
        limit=limit,
        sort=sort
    )
    return products

@router.get("/detail/{product_id}", response_model=ProductDetail)
async def get_product_detail(
    request: Request,
    product_id: str,
    bypass_cache: bool = Query(False, description="Bypass cache and fetch fresh data"),
    ttl: Optional[int] = Query(3600, description="Cache TTL in seconds")
):
    """Get detailed product information."""
    product = await services.get_product_detail(
        request=request,
        product_id=product_id,
        bypass_cache=bypass_cache,
        ttl=ttl
    )
    return product

@router.get("/trending-products", response_model=List[ProductResponse])
async def get_trending_products(
    request: Request,
    limit: int = Query(50),
    page: int = Query(1),
    user: UserIn = Depends(get_current_user)):
        
    return await services.list_products(request, "trending products", limit=limit, page=page, max_results=3)
    


@router.get("/cache/info/{url:path}")
async def get_cache_info(request: Request, url: str):
    """Get cache information for a URL."""
    return await services.get_cache_info(request, url)

@router.post("/cache/clear")
async def clear_cache(request: Request):
    """Clear all cached data."""
    await services.clear_cache(request)
    return {"message": "Cache cleared successfully"}

@router.post("/cache/cleanup")
async def cleanup_cache(request: Request):
    """Remove expired cache entries."""
    await services.remove_expired_cache(request)
    return {"message": "Expired cache entries removed"}

@router.post("/cache/ttl/{url:path}")
async def set_cache_ttl(
    request: Request,
    url: str,
    ttl: int = Query(..., description="New TTL in seconds")
):
    """Set TTL for a cached URL."""
    success = await services.set_cache_ttl(request, url, ttl)
    if success:
        return {"message": "Cache TTL updated successfully"}
    return {"message": "URL not found in cache"}













