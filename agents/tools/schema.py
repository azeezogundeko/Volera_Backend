from pydantic import BaseModel
from typing import Optional, List


class FilterAttributes(BaseModel):
    features: Optional[List[str]] = None
    category: Optional[str] = None

class PriceFilter(BaseModel):
    max: Optional[float] = None
    min: Optional[float] = None

class SearchFilter(BaseModel):
    price: Optional[PriceFilter] = None
    attributes: Optional[FilterAttributes] = None

class WebSearchRequest(BaseModel):
    search_query: str 
    filter: Optional[SearchFilter] = None
    n_k: int
    description: str
    mode: str 







