from typing import List, Optional, Literal

from appwrite.client import AppwriteException

from . import services
from .schema import ProductResponse, ProductDetail, WishListProductSchema
from ..auth.schema import UserIn
from ..auth.services import get_current_user
from .model import Product, WishList

from appwrite import query
from fastapi import APIRouter, Query, Request, Depends, Body
from fastapi.exceptions import HTTPException


router = APIRouter()


@router.post("/save_product")
async def save_product(product: ProductDetail, user: UserIn = Depends(get_current_user)):
    
    # if not product:
    #     raise HTTPException(status_code=404, detail="Product not found")

    print(product)

    return await services.save_product(product, user)


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
    # print(f"Length of products: {len(products)}")
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
    


@router.post("/check-saved")
async def check_product_saved(product_id: str = Body(), user: UserIn = Depends(get_current_user)):
    try:
        product = await WishList.get(user.id, product_id)
    except Exception as e:
        print(str(e))
        
        raise HTTPException(status_code=404, detail="Product not found")
    return product.to_dict()


@router.delete("/unsave_product")
async def unsave_product(product_id: str, user: UserIn = Depends(get_current_user)):
    try:
        w_product = await WishList.get(user.id, product_id)
    except AppwriteException:
        raise HTTPException(status_code=404, detail="Product not found")

    await WishList.delete(w_product.id)

    return {"message": "Product unsaved successfully"}


@router.get("/saved_products", response_model = List[WishListProductSchema])
async def get_saved_products(
    page: int = Query(1, description="Page number"),
    limit: int = Query(10, description="Results per page"),
    user: UserIn = Depends(get_current_user)):
    wishlists = await WishList.list([query.Query.equal("user_id", user.id)], limit=limit, offset=(page - 1) * limit)

    if wishlists["total"] == 0:
        return []

    products = []
    for w in wishlists["documents"]:
        product = await Product.read(w.product_id)
        products.append(product.to_dict())

    return products
 








# @router.get("/cache/info/{url:path}")
# async def get_cache_info(request: Request, url: str):
#     """Get cache information for a URL."""
#     return await services.get_cache_info(request, url)

# @router.post("/cache/clear")
# async def clear_cache(request: Request):
#     """Clear all cached data."""
#     await services.clear_cache(request)
#     return {"message": "Cache cleared successfully"}

# @router.post("/cache/cleanup")
# async def cleanup_cache(request: Request):
#     """Remove expired cache entries."""
#     await services.remove_expired_cache(request)
#     return {"message": "Expired cache entries removed"}

# @router.post("/cache/ttl/{url:path}")
# async def set_cache_ttl(
#     request: Request,
#     url: str,
#     ttl: int = Query(..., description="New TTL in seconds")
# ):
#     """Set TTL for a cached URL."""
#     success = await services.set_cache_ttl(request, url, ttl)
#     if success:
#         return {"message": "Cache TTL updated successfully"}
#     return {"message": "URL not found in cache"}










