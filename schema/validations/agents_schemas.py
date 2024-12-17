from typing import Literal, List

from pydantic import BaseModel



class MetaAgentSchema(BaseModel):
    next_node: Literal[
        "human_node", 
        "comparison_agent", 
        "shop_retrieval_agent",
        "reviewer_agent",
        "policy_agent",
        "writer_agent",
        "memory_agent"
        ]
    instructions: List[str]