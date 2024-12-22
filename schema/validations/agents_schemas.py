from typing import Literal, List, Dict, Any

from pydantic import BaseModel, field_validator


class BaseSchema(BaseModel):
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

class FilterAttrubuteSchema(BaseSchema):
    features: List[str]
    category: str
    brand_preferences: List[str]

class FilterSchema(BaseSchema):
    price: dict
    attributes : FilterAttrubuteSchema

class SearchParamSchema(BaseSchema):
    query: str
    filter: FilterSchema
    n_k: int
    semantic_description: str
    search_strategy: str

class RequirementSchema(BaseSchema):
    product_category: str
    product_type: str 
    purpose: str
    preferred_brands: List[str]
    specific_features: List[str] 
    budget: str

    @field_validator('preferred_brands', 'specific_features', mode='before')
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []

    @field_validator('product_type', mode='before')
    @classmethod
    def set_default_if_empty(cls, v):
        return v if v else ""

    def to_dict(self) -> Dict[str, Any]:
        return {
        k: v for k, v in self.model_dump().items() 
        if v is not None and v != "" and v != []
    }

    class Config:
        # Allow population by alias
        allow_population_by_field_name = True
        # Extra fields will be ignored instead of raising an error
        extra = 'ignore'

class FeedbackResponseSchema(BaseSchema):
    action: Literal["__user__", "__stop__"]
    reply: str
    requirements: RequirementSchema



class PlannerAgentSchema(BaseSchema):
    search_query: str
    product_retrieval_query: str
    filter: FilterSchema 
    n_k: int
    description: str
    writer_instructions: List[str]
    search_strategy: str

# class MetaAgentSchema(BaseModel):
    #     next_node: Literal[
#         "human_node", 
#         "comparison_agent", 
#         "insights_agent",
#         "reviewer_agent", 
#         # "shop_retrieval_agent",
#         # "policy_agent",
#         # "writer_agent",
#         # "memory_agent"
#         ]
#     instructions: List[str]


class SearchAgentSchema(BaseSchema):
    param: List[SearchParamSchema]

class ComparisonSchema(BaseSchema):
    content: str

class InsightsSchema(BaseSchema):
    content: str

class ReviewerSchema(BaseSchema):
    content: str

class PolicySchema(BaseSchema):
    compliant: bool
    violation: str
    reason: str

class HumanSchema(BaseSchema):
    content: str
