from __future__ import annotations

from datetime import datetime

from db._appwrite.fields import AppwriteField
from db._appwrite.model_base import AppwriteModelBase
from appwrite.query import Query



class PriceHistory(AppwriteModelBase):
    collection_id = "track_price_history"

    user_id: str = AppwriteField(size=255, required=True, type="string")
    tracked_id: str = AppwriteField(type="string", size=255, required=True)
    index = AppwriteField(type="index", index_type="key", index_attr=["user_id", "tracked_id"])
    timestamp: datetime = AppwriteField(type="datetime", required=True)
    price: float = AppwriteField(type="float", required=True, default=0.0)


    @classmethod
    async def get_current_price(cls, user_id: str, tracked_id: str)-> float:
        price_history = await super().list(
            queries=[
                Query.equal("user_id", user_id),
                Query.equal("tracked_id", tracked_id),
                Query.order_desc("timestamp")  
            ],
            limit=1  
        )
        if price_history["documents"]:
            return price_history["documents"].price  
        return 0.0  


class TrackedItem(AppwriteModelBase):

    collection_id = "tracked_item"

    user_id: str = AppwriteField(size=255, required=True, type="string")
    target_price: float = AppwriteField(type="float", required=True)
    current_price: float = AppwriteField(type="float", required=False)
    product_id: str = AppwriteField(size=255, required=True, type="string")
    notification_enabled: bool  = AppwriteField(required=False, type="bool", default=True)
    price_change: bool = AppwriteField(type="bool", default=False)
    alert_sent: bool = AppwriteField(required=False, type="bool", default=False)
    index = AppwriteField(type="index", index_type="key", index_attr=["user_id", "product_id"])
 
    
    @classmethod
    async def create(cls, product_id: str, tracked_price: float, current_price: float, user_id: str)-> TrackedItem:
        return await super().create(
            document_id=cls.get_unique_id(),
            data={"product_id": product_id, "target_price": tracked_price, "user_id": user_id, "current_price": current_price}
        )

# class Product(AppwriteModelBase):
#     collection_id = "product"

#     current_price: float  = AppwriteField(type="float", required=True, default=0.0)
#     image: str = AppwriteField(size=255, required=False, type="string")
#     date_added:  datetime =  AppwriteField(type="datetime", required=True)
#     currency: str = AppwriteField(size=5, required=True, type="string", default="₦")
#     title: str = AppwriteField(size=255, required=True, type="string")
#     url: AppwriteField(size=255, required=True, type="string")
#     features: List[str] = AppwriteField(required=True, type="array", default=[])
#     specifications: List[Specification] = AppwriteField(required=True, type="array", default=[])


# class TrackedItem(AppwriteModelBase):

#     collection_id = "track_tracked_item"
#     user_id: str = AppwriteField(size=40, required=True, type="string")
#     alert_price: float  = AppwriteField(size=40, required=True, type="float")
#     alert_sent: bool = AppwriteField(required=True, type="bool", default=False)
#     target_price: float  = AppwriteField(size=40, required=True, type="float")
#     product_id: str = AppwriteField(size=255, required=True, type="string")
