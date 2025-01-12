from datetime import datetime
from pydantic import BaseModel, Field, field_validator
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
    

class TrackedItemSchema(BaseModel):
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
    specifications: List[FeatureSchema]
    # specs: List[FeatureSchema]
    # price_history = List[PriceHistorySchema]

    @field_validator("specifications", mode="before")
    def validate_specifications(cls, v):
        # Ensure 'specifications' is a list, otherwise try to convert it.
        if isinstance(v, str):
            # Attempt to parse the string as JSON to convert it into a list of FeatureSchema objects
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Specifications should be a valid list or a JSON string representing a list.")
        return v

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


