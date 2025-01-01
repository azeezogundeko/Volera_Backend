from typing import List, Literal
from unicodedata import category
from schema.validations.agents_schemas import BaseSchema, Field


class SearchSchema(BaseSchema):
    search_query: str = ""
    category: str = Field(description="Category of the search")


class WebQueryAgentSchema(BaseSchema):
    search_query: str = ""
    content : str = ""
    action: str


class SummaryAgentSchema(BaseSchema):
    content: str
    category: str
