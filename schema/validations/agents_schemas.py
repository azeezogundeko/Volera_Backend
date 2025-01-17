import math
from typing import Literal, List, Dict, Any

from pydantic import BaseModel, field_validator, Field


class BaseSchema(BaseModel):
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> Dict[str, Any]:
        return self.model_dump(mode='json')

    class Config:
        json_encoders = {
            float: lambda v: float(v) if not math.isinf(v) else None
        }


class FilterAttributesSchema(BaseSchema):
    features: List[str] = Field(default_factory=list)
    category: str = ""
    brand_preferences: List[str] = Field(default_factory=list)

class PriceRangeSchema(BaseSchema):
    min: float = Field(default=0.0)
    max: float = Field(default=float('inf'))

class DiscountRangeSchema(BaseSchema):
    min: float = Field(default=0.0)
    max: float = Field(default=100.0)

class FilterSchema(BaseSchema):
    price: PriceRangeSchema = Field(default_factory=PriceRangeSchema)
    discount: DiscountRangeSchema = Field(default_factory=DiscountRangeSchema)
    attributes: FilterAttributesSchema = Field(default_factory=FilterAttributesSchema)


class PlannerAgentSchema(BaseSchema):
    search_query: str = ""
    product_retriever_query: str = Field(
        ..., 
        description="Must be in format 'product brand category', e.g. 'iPhone 15 Pro Apple Smartphones'"
    )
    filter: FilterSchema = Field(default_factory=FilterSchema)
    n_k: int = 5
    description: str = Field(
        ..., 
        description="Mandatory detailed description of search intent rich in semantic meanings"
    )
    writer_instructions: List[str] = Field(default_factory=list)
    search_strategy: str = "adaptive"




    
class SearchParamSchema(BaseSchema):
    query: str
    filter: FilterAttributesSchema = Field(default_factory=FilterAttributesSchema)
    n_k: int
    semantic_description: str
    search_strategy: str

class RequirementSchema(BaseSchema):
    product_category: str
    key_preferences: List[str] 
    purpose: str


# class MetaAgentSchema(B)
    # preferred_brands: List[str]
    # specific_features: List[str] 
    # budget: str

    # @field_validator('preferred_brands', 'specific_features', mode='before')
    # @classmethod
    # def ensure_list(cls, v):
    #     if isinstance(v, str):
    #         return [v]
    #     return v or []

    # @field_validator('product_type', mode='before')
    # @classmethod
    # def set_default_if_empty(cls, v):
    #     return v if v else ""

    # def to_dict(self) -> Dict[str, Any]:
    #     return {
    #     k: v for k, v in self.model_dump().items() 
    #     if v is not None and v != "" and v != []
    # }

    # class Config:
    #     # Allow population by alias
    #     populate_by_name = True
    #     # Extra fields will be ignored instead of raising an error
    #     extra = 'ignore'

class FeedbackResponseSchema(BaseSchema):
    action: Literal["__user__", "__stop__"]
    reply: str
    requirements: RequirementSchema


class MetaAgentSchema(BaseSchema):
    action: str
    content: str
    requirements: RequirementSchema

class FollowAgentSchema(BaseSchema):
    action: str
    content: str
    user_query: str



class SearchAgentSchema(BaseSchema):
    param: List[SearchParamSchema]

class ComparisonSchema(BaseSchema):
    content: str

class InsightsSchema(BaseSchema):

    content: str

class ReviewerSchema(BaseSchema):
    content: str = Field(description="The content of the writing")

class PolicySchema(BaseSchema):
    compliant: bool
    violation: str
    reason: str

class HumanSchema(BaseSchema):
    content: str



class WebSchema(BaseSchema):
    content: str

class MetaAgentSchema(BaseSchema):
    action: str
    content: str
    requirements: RequirementSchema

    class Config:
        # Allow population by alias
        populate_by_name = True
        # Extra fields will be ignored instead of raising an error
        extra = 'ignore'
