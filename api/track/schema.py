from datetime import datetime
from pydantic import BaseModel, Field
from typing import List

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
    

class ProductSchema(BaseModel):
    product_id: str
    title: str
    url: str
    current_price: float = Field(serialization_alias="currentPrice")
    target_price: float = Field(serialization_alias="targetPrice")
    image: str
    date_added: datetime = Field(serialization_alias="dateAdded")
    notification_enabled: bool 
    currency: str = "₦"
    features: List[str]
    specs: List[FeatureSchema]
    price_history = List[PriceHistorySchema]


