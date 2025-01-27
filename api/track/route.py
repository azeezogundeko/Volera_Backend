from typing import List

from appwrite.client import AppwriteException

from .schema import (
    DashBoardStat, 
    PriceHistorySchema,
    TrackedItemSchema,
    DetailedTrackedItemSchema,
    TrackItemIn,
    TrackedItemOut
    )

from .model import PriceHistory, TrackedItem
from ..auth.services import get_current_user
from ..chat.model import Chat
from ..auth.schema import UserIn
from ..product.model import Product
from ..product.services import save_product
from .scrape import EcommerceWebScraper

from utils.logging import logger

from appwrite import query
from fastapi import APIRouter, Request, Depends, Query


router = APIRouter()


@router.get("/stats", response_model=DashBoardStat)
async def get_stats(user: UserIn = Depends(get_current_user)):

    try:
    
        chat_count = await Chat.count([query.Query.equal("user_id", user.id)])
        tracked_items = await TrackedItem.count([query.Query.equal("user_id", user.id)])
        price_alerts   = await TrackedItem.count(
            [query.Query.equal("user_id", user.id), query.Query.equal("alert_sent", True)])

        return {
            "chat_count": chat_count,
            "tracked_items_count": tracked_items,
            "price_alerts": price_alerts,
        }
    except Exception:
        return {"chat_count": 0, "tracked_items_count": 0, "price_alerts": 0}


@router.get("/price-history", response_model=List[PriceHistorySchema])
async def get_price_history(
    limit: int = Query(25),
    page: int = Query(1),
    user: UserIn = Depends(get_current_user)):
    try:
        response = await PriceHistory.list(
            limit=limit, offset=(page - 1) * limit, queries=[query.Query.equal("user_id", user.id)])

        return response["documents"]

    except AppwriteException as e:
        logger.error(e.message)
        return []

@router.get("/price-history/{product_id}", response_model=List[PriceHistorySchema])
async def get_price_history(
    product_id: str, 
    user: UserIn = Depends(get_current_user)
    ):
    
    documents = await PriceHistory.list([
        query.Query.equal("product_id", product_id), 
        query.Query.equal("user_id", user.id)
        ]
    )
    return documents["documents"]


@router.get("", response_model=List[TrackedItemOut])
async def get_tracked_items(
    limit: int = Query(50),
    page: int = Query(1),
    user: UserIn = Depends(get_current_user)):
    
    r = await TrackedItem.list(
        [query.Query.equal("user_id", user.id)], 
            limit=limit, offset=(page - 1) * limit)

    products = []

    for tracked_item in r["documents"]:
        product = await Product.read(tracked_item.product_id)
        products.append(product)

    responses = []
    for r, product in zip(r["documents"], products):
        responses.append({
            "id": r.id,
            "productId": r.product_id,
            "product": product.to_dict(),
            "targetPrice": r.target_price,
            "currentPrice": r.current_price,
            "dateAdded": r.created_at,
            "notificationEnabled": r.notification_enabled,
            "alertSent": r.alert_sent,
            
        })

    return responses


@router.get("/{product_id}", response_model=DetailedTrackedItemSchema)
async def get_tracked_item(product_id: str, user: UserIn = Depends(get_current_user)):

    tracked_item = await TrackedItem.read(product_id, [query.Query.equal("user_id", user.id)])
    price_history = await PriceHistory.list(
        [
            query.Query.equal("product_id", product_id), 
            query.Query.equal("user_id", user.id)
            ]
        )["documents"]
    return {"tracked_item": tracked_item, "price_history": price_history}


@router.post("", response_model=TrackedItemSchema)
async def track_item(
    request: Request,
    payload: TrackItemIn,
    user: UserIn = Depends(get_current_user)
    ):
    await save_product(payload.product, user)
    return await TrackedItem.create(payload.productId, payload.targetPrice, payload.product.current_price, user.id)
         

@router.post("test")
async def test_scrape(
    url: str,
    source: str
):
    scraper = EcommerceWebScraper()
    results = await scraper.get_product_details(url, source)
    print(results)
    return results