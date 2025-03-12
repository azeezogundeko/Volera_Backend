import os
import json
import asyncio


from pydantic import BaseModel, Field
from typing import List, List
from crawl4ai import CrawlerRunConfig, CacheMode, AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from utils._craw4ai import CrawlerManager
from .prompt import product_extractor_prompt

from schema.dataclass.dependencies import get_next_serp_api_key


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
    # comment: str = Field(description="Comment on the results")
    

class ProductExtractor:
    def __init__(
            self, 
            api_key: str = None, 
            schema: BaseModel = Product,
            llm_provider: str = "gemini/gemini-2.0-flash", 
            ):
        
        self.api_key = api_key
        self.schema: BaseModel = schema
        self.llm_provider = llm_provider
        self.crawl_config = self._create_crawl_config()

    def _create_crawl_config(self):
        return CrawlerRunConfig(
            excluded_tags=["nav", "footer", "header", "script", "style"],
            extraction_strategy=LLMExtractionStrategy(
                provider=self.llm_provider,
                api_token=self.api_key,
                schema=self.schema.model_json_schema(),
                extraction_type="schema",
                instruction=product_extractor_prompt,
                chunk_token_threshold=2000,
                overlap_rate=0.1,
                apply_chunking=True,
                input_format="markdown",
                extra_args={"temperature": 0.1, "max_tokens": 1500},
                verbose=True
            ),
            cache_mode=CacheMode.BYPASS
        )

    async def extract_products(self, urls: List[str]):
        results = {}
        crawler = await CrawlerManager.get_crawler() 
        tasks = [self._process_url(crawler, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return {url: result for url, result in zip(urls, results)}

    async def _process_url(self, crawler: AsyncWebCrawler, url):
        try:
            result = await crawler.arun(url=url, config=self.crawl_config)
            if result.success:
                return json.loads(result.extracted_content)
            return {"error": result.error_message}
        except Exception as e:
            return {"error": str(e)}

extractor = ProductExtractor(
    api_key=get_next_serp_api_key()
)
