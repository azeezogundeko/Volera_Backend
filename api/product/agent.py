from pydantic_ai import Agent

from .prompt import query_system_prompt
from pydantic import BaseModel, Field, field_validator
from schema import GeminiDependencies #, GroqDependencies
# from typing import List, Any, Literal, Optional


class Sort(BaseModel):
    key: str
    reverse: bool 

class Filter(BaseModel):
    category: str 
    price: float = Field(default=0.0)
    brand: str = ''

    @field_validator("price", mode="after")
    def validate_price(cls, v):
        if v is not None and v <= 0:
            return None
        return v

    @field_validator("category", mode="after")
    def validate_categories(cls, v):
        if v is None or not v:
            return None
        return v  # Return the original value if it's valid

    @field_validator("brand", mode="after")
    def validate_brand(cls, v):
        if v == '':
            return None
        return v


class QueryAgentSchema(BaseModel):
    reviewed_query: str
    filter: Filter
    sort: str

query_agent = Agent(
    model="gemini-1.5-flash",
    system_prompt=query_system_prompt,
    result_type=QueryAgentSchema,
    retries=2,
    deps_type=GeminiDependencies,
    name="Query Reviser Agent"
)
