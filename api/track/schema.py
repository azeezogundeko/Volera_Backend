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
    date: datetime
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


class TrackItemIn(BaseModel):
    productId: str
    targetPrice: float
    product: ProductDetail


class TrackedItemOut(BaseModel):
    id:  str
    notificationEnabled: bool 
    currentPrice: float
    product: WishListProductSchema
    alertSent: bool
    dateAdded: datetime
    productId: str
    targetPrice: float
