from typing import Literal, List

from pydantic import BaseModel



class MetaAgentSchema(BaseModel):
    next_node: Literal[
        "human_node", 
        "comparison_agent", 
        "insights_agent",
        "reviewer_agent", 
        # "shop_retrieval_agent",
        # "policy_agent",
        # "writer_agent",
        # "memory_agent"
        ]
    instructions: List[str]

class SearchParamSchema(BaseModel):
    query: str
    filter: str
    n_k: int
    semantic_description: str

class SearchAgentSchema(BaseModel):
    params: List[SearchParamSchema]

class ComparisonSchema(BaseModel):
    content: str

class InsightsSchema(BaseModel):
    content: str

class ReviewerSchema(BaseModel):
    content: str

class PolicySchema(BaseModel):
    compliant: bool
    violation: str
    reason: str

class HumanSchema(BaseModel):
    content: str
