from typing import List, Optional, Literal

from appwrite.client import AppwriteException

from . import services
from .agent import query_agent
from .schema import ProductResponse, ProductDetail, WishListProductSchema, SearchRequest
from ..auth.schema import UserIn
from ..auth.services import get_current_user
from .model import Product, WishList
from utils.logging import logger
from utils.image import image_analysis, get_product_prompt, IMAGE_DESCRIPTION_PROMPT

from appwrite import query
from fastapi import APIRouter, Query, Request, Depends, Body
from fastapi.exceptions import HTTPException
import asyncio


router = APIRouter()


@router.post("/save_product")
async def save_product(product: ProductDetail, user: UserIn = Depends(get_current_user)):
    return await services.save_product(product, user)


@router.post("/search", response_model=List[ProductResponse])
async def search_products(
    request: Request,
    payload: SearchRequest = Depends(),
    
):
    "" "Search for products across supported e-commerce sites."""
    query = payload.query
    sort=None
    if payload.images is not None:
        image_data = await asyncio.gather(*(image.read() for image in payload.images))
        description = await image_analysis(
            image_data,
             get_product_prompt(query, 
             IMAGE_DESCRIPTION_PROMPT)
             )
        logger.info(f"Image analysis result: {query}")


        query = f"""
        USER QUERY: {query}

        IMAGE DESCRIPTIONS: {description}
        
        """

    try:
        response = await query_agent.run(query)
        result = response.data
        query = result.reviewed_query
        sort=result.sort
    except Exception as e:
        logger.error(f"Error running query agent: {e}")
    
    ecommerce_manager = services.get_ecommerce_manager(request)
    products = await services.list_products(
        ecommerce_manager=ecommerce_manager,
        query=query,
        site=payload.site,
        max_results=payload.max_results,
        bypass_cache=payload.bypass_cache,
        page=payload.page,
        limit=payload.limit,
        sort=sort,
        filters=result.filter.__dict__
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
    manager = services.get_ecommerce_manager(request)
    product = await services.get_product_detail(
        ecommerce_manager=manager,
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
        
    manager = services.get_ecommerce_manager(request)
        
    return await services.list_products(manager, "trending products", limit=limit, page=page, max_results=3)
    


@router.post("/check-saved")
async def check_product_saved(product_id: str = Body(), user: UserIn = Depends(get_current_user)):
    try:
        product = await WishList.get(user.id, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
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
 