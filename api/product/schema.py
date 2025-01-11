from token import OP
from typing import List, Optional
from pydantic import BaseModel, field_validator

class Image(BaseModel):
    url: Optional[str] = None
    zoom_url: Optional[str] = None
    alt: Optional[str] = "No description available"

class ProductBasicInfo(BaseModel):
    name: Optional[str] = "Unknown Product"
    current_price: Optional[float] = 0.0
    original_price: Optional[float] = 0.0
    brand: Optional[str] = "Unknown Brand"
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

    # @field_validator("rating", mode='before')
    # def convert_rating(cls, v):
    #     "convert rating to float"
    #     if isinstance(v, str):
    #         return float(v.replace('out of 5', ''))
    #     return v

    # @field_validator("discount", mode='before')
    # def convert_discount(cls, v):
    #     "convert discount to float"
    #     if isinstance(v, str):
    #         return float(v.replace('%', ''))
    #     return v

    # @field_validator('current_price', 'original_price', mode='before')
    # def convert_price(cls, v):
    #     "convert price to float"
    #     if isinstance(v, str):
    #         # Remove currency symbol and any whitespace
    #         v = v.replace('₦', '').strip()
    #         # Remove commas and convert to float
    #         try:
    #             return float(v.replace(',', ''))
    #         except (ValueError, TypeError):
    #             return 0.0
    #     return v if v is not None else 0.0

class Feature(BaseModel):
    feature: Optional[str] = "No feature specified"

class Specification(BaseModel):
    value: Optional[str] = "No value specified"
    key: Optional[str] = "No key specified"


    @field_validator('value', mode='before')
    def convert_value(cls, v):
        if v is None:
            return "No value specified"
        v = v.strip()
        if ':' not in v:
            return v
        return v.split(':')[1].strip()

class ProductDetail(BaseModel):
    features: Optional[List[str]] = []
    specifications: Optional[List[Specification]] = []

    @field_validator('features', mode='before')
    def convert_features(cls, v):
        if isinstance(v, list):
            print(v)
            return [feature["feature"] for feature in v if isinstance(feature, dict)]
        return v

class Review(BaseModel):
    rating: Optional[float] = 0.0
    title: Optional[str] = "No title"
    comment: Optional[str] = "No comment"
    date: Optional[str] = "Unknown date"
    author: Optional[str] = "Anonymous"

    @field_validator("rating", mode='before')
    def convert_rating(cls, v):
        "convert rating to float"
        if isinstance(v, str):
            return float(v.replace('out of 5', ''))
        return v

class ProductReviews(BaseModel):
    reviews: Optional[List[Review]] = []

class ProductSchema(BaseModel):
    source: Optional[str] = "Unknown source"
    category: Optional[str] = "Uncategorized"
    product_basic_info: Optional[ProductBasicInfo] = ProductBasicInfo()
    product_details: Optional[List[ProductDetail]] = []
    product_reviews: Optional[ProductReviews] = ProductReviews()


class ProductResponse(BaseModel):
    name: Optional[str] = "Unknown Product"
    current_price: Optional[float] = 0.0
    original_price: Optional[float] = 0.0
    brand: Optional[str] = "Unknown Brand"
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
