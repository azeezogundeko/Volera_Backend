from typing import List, Optional, Literal
import time

from appwrite.client import AppwriteException

from . import services
from .agent import query_agent
from .schema import ProductResponse, ProductDetail, WishListProductSchema, SearchRequest
from ..auth.schema import UserIn
from ..track.scrape import scraper
from ..auth.services import get_current_user
from .model import Product, WishList

from utils.logging import logger
from utils.decorator import credit_required
from utils.queue import processing_semaphore, determine_priority, request_queues,  QUEUE_TIMEOUT, limiter
from utils.image import image_analysis, get_product_prompt, IMAGE_DESCRIPTION_PROMPT

from appwrite import query
from fastapi import APIRouter, Query, Request, Depends, Body, status
from fastapi.exceptions import HTTPException
import asyncio



router = APIRouter()


@router.post("/save_product")
async def save_product(product: ProductDetail, user: UserIn = Depends(get_current_user)):
    return await services.save_product(product, user)


@router.post("/search", response_model=List[ProductResponse])
@limiter.limit(times=100, minutes=1) 
@credit_required(10)
async def search_products(
    request: Request,
    payload: SearchRequest = Depends()
):
    """Optimized search endpoint with queueing and prioritization"""
    try:
        # Try immediate processing
        if processing_semaphore.locked():
            priority = determine_priority(request.state.user)
            response_channel = asyncio.Queue(maxsize=1)
            
            if request_queues[priority].full():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Queue overflow"
                )
                
            await request_queues[priority].put({
                "request": request,
                "payload": payload,
                "response_channel": response_channel,
                "timestamp": time.time()
            })
            
            try:
                result = await asyncio.wait_for(
                    response_channel.get(),
                    timeout=QUEUE_TIMEOUT
                )
                if "error" in result:
                    raise HTTPException(500, result["error"])
                return result
            except asyncio.TimeoutError:
                raise HTTPException(504, "Queue processing timeout")

        # Process immediately if capacity available
        async with processing_semaphore:
            return await process_request(request.state.user, request, payload)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critical system error: {str(e)}")
        raise HTTPException(500, "Internal server error")


async def process_request(user: UserIn, request: Request, payload: SearchRequest):
    """Core request processing with enhanced error handling"""
    try:
        # Image processing
        query = payload.query
        if payload.images:
            image_data = await asyncio.gather(
                *(image.read() for image in payload.images)
            )
            description = await image_analysis(
                image_data,
                get_product_prompt(query, IMAGE_DESCRIPTION_PROMPT)
            )
            logger.info(f"Image analysis completed: {query[:50]}...")
            query = f"USER QUERY: {query}\nIMAGE DESCRIPTIONS: {description}"

        # Query agent execution
        response = await query_agent.run(query)
        result = response.data
        processed_query = result.reviewed_query
        sort_params = result.sort
        filter_params = result.filter.__dict__

        # Product listing
        ecommerce_manager = services.get_ecommerce_manager(request)
        products = await services.list_products(
            ecommerce_manager=ecommerce_manager,
            query=processed_query,
            site=payload.site,
            max_results=payload.max_results,
            bypass_cache=payload.bypass_cache,
            page=payload.page,
            limit=payload.limit,
            sort=sort_params,
            filters=filter_params
        )
        
        return products

    except asyncio.CancelledError:
        logger.warning("Request processing cancelled")
        raise
    except Exception as e:
        logger.error(f"Processing failure: {str(e)}")
        raise


async def queue_worker(priority_level: int):
    """Process queued requests with priority handling"""
    while True:
        request_data = await request_queues[priority_level].get()
        async with processing_semaphore:
            try:
                result = await process_request(
                    request_data["request"],
                    request_data["payload"]
                )
                await request_data["response_channel"].put(result)
            except Exception as e:
                await request_data["response_channel"].put({
                    "error": f"Priority {priority_level} processing failed: {str(e)}"
                })
            finally:
                request_queues[priority_level].task_done()


# @credit_required(2)
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
    
    if product is None:
        # try:
        #     product = await Product.read(product_id)
        #     product = product.to_dict()
        #     product["product_id"] = product.pop("$id")
        # except AppwriteException:
        try:
            product = await scraper.get_product_details(product_id)
            print(product)
            await manager.db_manager.set(
                    key=product_id,
                    value=product,
                    tag="detail",
                )
        except Exception as e:
            logger.error(str(e), exc_info=True)
            raise HTTPException(404, "Failed to Search")

    print(product)

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
 