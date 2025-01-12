from typing import List, Optional
from pydantic import BaseModel, field_validator
from datetime import datetime

class Image(BaseModel):
    url: Optional[str] = None
    zoom_url: Optional[str] = None
    alt: Optional[str] = None

class Seller(BaseModel):
    name: Optional[str] = None
    rating: Optional[float] = 0.0

class Specification(BaseModel):
    label: Optional[str] = None
    value: Optional[str] = None

class Review(BaseModel):
    rating: Optional[float] = 0.0
    title: Optional[str] = None
    comment: Optional[str] = None
    date: Optional[str] = None
    author: Optional[str] = None
    verified: Optional[bool] = False

class Stock(BaseModel):
    in_stock: Optional[bool] = False
    quantity: Optional[int] = 0
    quantity_sold: Optional[int] = 0
    min_sale_qty: Optional[int] = 1
    max_sale_qty: Optional[int] = 0

class ProductDetail(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    currency: Optional[str] = "₦"
    description: Optional[str] = None
    current_price: Optional[float] = 0.0
    original_price: Optional[float] = 0.0
    discount: Optional[float] = 0.0
    url: Optional[str] = None
    image: Optional[str] = None
    images: Optional[List[Image]] = []
    source: Optional[str] = None
    rating: Optional[float] = 0.0
    rating_count: Optional[int] = 0
    seller: Optional[Seller] = None
    specifications: Optional[List[Specification]] = []
    features: Optional[List[str]] = []
    reviews: Optional[List[Review]] = []
    stock: Optional[Stock] = None
    is_free_shipping: Optional[bool] = False
    is_pay_on_delivery: Optional[bool] = False
    express_delivery: Optional[bool] = False
    is_official_store: Optional[bool] = False


class ProductResponse(BaseModel):
    name: Optional[str] = "Unknown Product"
    current_price: Optional[float] = 0.0
    original_price: Optional[float] = 0.0
    brand: Optional[str] = "Unknown Brand"
    category: Optional[str] = "Unknown Category"
    discount: Optional[float] = 0.0
    rating: Optional[float] = 0.0
    reviews_count: Optional[str] = "0"
    product_id: Optional[str] = None
    image: Optional[str] = None
    relevance_score: float = 0.0
    url: Optional[str] = None
    # images: Optional[List[Image]] = []
    currency: Optional[str] = "₦"
    source: Optional[str] = "Unknown source"

    @field_validator("relevance_score", mode="before")
    def validate_relevance_score(cls, v):
        import numpy as np
        if isinstance(v, np.float32):
            return float(v)

        else:
            return v
