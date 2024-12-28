from typing import List

from pydantic import Field
from schema.validations.agents_schemas import BaseSchema

class WebPlannerAgentSchema(BaseSchema):
    search_query: str 
    n_k: int = 5
    description: str = Field(
        ..., 
        description="Mandatory detailed description of search intent rich in semantic meanings"
    )
    writer_instructions: List[str] = Field(default_factory=list)