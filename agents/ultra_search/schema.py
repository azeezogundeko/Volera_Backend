from pydantic import BaseModel, Field
from typing import List
from schema.validations.agents_schemas import BaseSchema


class Query(BaseSchema):
    site: str = Field(description='site to perform search on')
    query: str = Field(description='reviewed search query format <BRAND> <NAME> <REGION>')
    source: str = Field(description='source for the website to search eg jumia, jiji')


class PlannerSchema(BaseSchema):
    no_of_results: int = 10
    action: str = Field(description='action to take __user__, __research__, user of asking question and research to start research')
    researcher_agent_instructions: List[str] = []
    filter_criteria: str = ''
    content: str = Field(default='', description="your response to the user")
    search_queries: List[Query] = Field(default=[])
    comment: str = Field(default=[], description='Summary of to take')

class ReviewerSchema(BaseSchema):
    status: str = Field(description="__failed__ if all products did not meet the requirements else __passed__ if any met")
    product_ids: List[str] = Field(description="list of passed product ids")
    comment: str = Field(description='A summary of your decision process and why your final decision')


class ResponseSchema(BaseSchema):
    comment: str = Field(description='A summary of your decision process and why your final decision')
    product_ids: List[str] = []
    response: str = Field(description="Your advice, recommendations to the user based on the returned products")


class Specification(BaseModel):
    label: str 
    value: str 

class ProductDetail(BaseModel):
    name: str = Field(description="Name of the product")
    brand: str = Field(description="Brand of the product")
    category: str = Field('', description="Category of the product")
    currency: str = Field(description="Currency symbol for the price (default is Naira '₦')")
    description: str = Field(description="Detailed description of the product")
    current_price: float = Field(description="Current selling price of the product")
    original_price: float = Field(0.0, description="Original price before any discount")
    discount: float = Field(0.0, description="Discount amount applied to the product")
    url: str = Field(description="Direct URL to the product page")
    image: str = Field(description="URL of the product image")
    source: str = Field(description="The source of the product, e.g., Amazon, Jumia, Konga, etc.")
    rating: float = Field(0.0, description="Average user rating of the product")
    rating_count: int = Field(0, description="Total number of ratings received")
    specifications: List[Specification] = Field(default_factory=list, description="List of key-value specifications for the product")
    features: List[str] = Field(default_factory=list, description="List of notable features of the product")

class Product(BaseModel):
    products: List[ProductDetail] = []
    comment: str = Field(description="Comment on the results")
    

class IntentAnalysis(BaseModel):
    primary_goal: str
    product_category: str
    key_features: List[str]
    constraint: List[str]

class ResultSchema(BaseSchema):
    reviewed_query: str
    # intent_analysis: IntentAnalysis