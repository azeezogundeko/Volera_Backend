from datetime import datetime
from pydantic import BaseModel, Field
from typing import List

from ..product.schema import ProductDetail, ProductResponse, WishListProductSchema

class FeatureSchema(BaseModel):
    label: str
    value: str

class PriceHistorySchema(BaseModel):
    timestamp: datetime
    price: float

class ProductIn(BaseModel):
    title: str
    url: str
    current_price: float
    image: str
    date_added: datetime
    notification_enabled: bool= True
    currency: str = "₦"
    alert_sent: bool = False
    

class TrackedItemSchema(BaseModel):
    product_id: str = Field(serialization_alias="productId")
    target_price: float = Field(serialization_alias="targetPrice")
    created_at: datetime = Field(serialization_alias="dateAdded")
    notification_enabled: bool = Field(serialization_alias="notificationEnabled")
    alert_sent: bool = Field(serialization_alias="alertSent")


    

class PriceHistorySchema(BaseModel):
    timestamp: datetime
    price: float

class DetailedTrackedItemSchema(BaseModel):
    tracked_item: TrackedItemSchema
    price_history: List[PriceHistorySchema]

class DashBoardStat(BaseModel):
    active_chat: int = Field(default=0, serialization_alias="activeChat")
    tracked_items: int = Field(default=0, serialization_alias="trackedItems")
    price_alerts: int = Field(default=0, serialization_alias="priceAlerts")

class Product(ProductResponse):
    product_id: str = Field(serialization_alias="productId", alias="id")

# class ProductIn(ProductDetail):
#     class Config:
#         model_config = {
#             "from_attributes": True,
#             "exclude": {
#                 "product_id",
#                  "date_added", 
#                  "rating_count", 
#                  "reviews", 
#                  "reviews_count", 
#                  "stock", 
#                  "is_free_shipping", 
#                  "is_official_store", 
#                  "is_pay_on_delivery", 
#                  "express_delivery",
#                  "categories",
#                  "description",
#                  "images",
#                  "seller",
#                  "original_price",
#                  },
#         }

class TrackItemIn(BaseModel):
    productId: str
    targetPrice: float
    product: ProductDetail

# class TrackProduct(BaseModel):
#     current_price: float
#     url: str
#     image: str
#     name: str
#     source: str
#     brand: str
#     reviews_count:int
#     discount: float
#     specifica

class TrackedItemOut(BaseModel):
    id:  str
    notificationEnabled: bool 
    currentPrice: float
    product: WishListProductSchema
    alertSent: bool
    dateAdded: datetime
    productId: str
    targetPrice: float
