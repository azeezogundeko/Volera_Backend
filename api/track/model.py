from datetime import datetime
from typing import List, TypedDict

from db._appwrite.model_base import AppwriteModelBase, AppwriteField



class PriceHistory(AppwriteModelBase):
    collection_id = "track_price_history"

    user_id: str = AppwriteField(size=255, required=True, type="string")
    product_id: str = AppwriteField(type="string", size=255, required=True)
    index = AppwriteField(type="index", index_type="unique", index_attr=["user_id", "product_id"])
    timestamp: datetime = AppwriteField(type="datetime", required=True)
    price: float = AppwriteField(type="float", required=True, default=0.0)


class TrackedItem(AppwriteModelBase):

    collection_id = "tracked_item"

    user_id: str = AppwriteField(size=255, required=True, type="string")
    index = AppwriteField(type="index", index_type="unique", index_attr=["user_id", "product_id"])
    product_id: str = AppwriteField(size=255, required=True, type="string")
    notification_enabled: bool  = AppwriteField(required=True, type="bool")
    last_scraped_at: datetime = AppwriteField(type="datetime", required=False)
    price_change: bool = AppwriteField(type="bool", default=False)
    alert_sent: bool = AppwriteField(required=True, type="bool", default=False)
 

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


