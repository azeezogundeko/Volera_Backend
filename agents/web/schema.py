# from typing import List

# from pydantic import Field
from schema.validations.agents_schemas import BaseSchema

class WebQueryAgentSchema(BaseSchema):
    search_query: str = ""
    content : str = ""
    action: str
    