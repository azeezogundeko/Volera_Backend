from datetime import datetime
from db._appwrite.model_base import AppwriteModelBase, AppwriteField


class Feature(AppwriteModelBase):

    collection_id = "track_feature"
    label: str = AppwriteField(size=255, required=True)
    value:  str = AppwriteField(size=255, required=True)
    product_id: str = AppwriteField(size=255, required=True)


class PriceHistory(AppwriteModelBase):
    collection_id = "track_price_history"
    timestamp: datetime = AppwriteField(type="datetime", required=True)
    price: float = AppwriteField(type="float", required=True, default=0.0)
    product_id: str = AppwriteField(type="string", size=255, required=True, )


class Product(AppwriteModelBase):
    collection_id = "track_product"
    product_id: str = AppwriteField(size=255, required=True, type="string")
    title: str = AppwriteField(size=255, required=True, type="string")
    url: AppwriteField(size=255, required=True, type="string")
    current_price: float  = AppwriteField(type="float", required=True, default=0.0)
    image: str = AppwriteField(size=255, required=True, type="string")
    date_added:  datetime =  AppwriteField(type="datetime", required=True)
    notification_enabled: bool  = AppwriteField(required=True, type="bool")
    currency: str = AppwriteField(size=5, required=True, type="string", default="₦")
    last_scraped_at: datetime = AppwriteField(type="datetime", required=True)
 
class TrackedItem(AppwriteModelBase):
    collection_id = "track_tracked_item"
    user_id: str = AppwriteField(size=40, required=True, type="string")
    alert_price: float  = AppwriteField(size=40, required=True, type="float")
    alert_sent: bool = AppwriteField(required=True, type="bool", default=False)
    target_price: float  = AppwriteField(size=40, required=True, type="float")
    product_id: str = AppwriteField(size=255, required=True, type="string")


