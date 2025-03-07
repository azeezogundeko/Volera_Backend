import os
import json
import asyncio
from pydantic import BaseModel, Field
from typing import List, Optional
from crawl4ai import CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from ._craw4ai import CrawlerManager

from schema import GroqDependencies, GeminiDependencies

class ProductExtractor:
    # def __init__(self, llm_provider: str = "openai/gpt-4o", api_token: str = None):
    #     self.crawl_config = self._create_crawl_config()

    def create_crawl_config(self, Schema: BaseModel, llm_provider: str = 'gemini/gemini-1.5-flash', api_token: str = GeminiDependencies.api_key):
        return CrawlerRunConfig(
            extraction_strategy=LLMExtractionStrategy(
                provider=llm_provider,
                api_token=api_token,
                schema=Schema.model_json_schema(),
                extraction_type="schema",
                instruction=(
                    "Extract product information including name, price, description, features, rating, and image URL. "
                    "Ensure that the extracted product has a valid 'name', 'url', 'source', 'description', and 'current_price'. "
                    "If any of these fields are missing or empty, do not return the product. "
                    "Do not include placeholder values, inaccurate information, or inferred details. "
                    "Ignore promotional content, related products, and advertisements. "
                    "Focus only on the main product details."
                    "Return list of the results"
                ),
                chunk_token_threshold=1500,
                overlap_rate=0.1,
                apply_chunking=True,
                input_format="markdown",
                extra_args={"temperature": 0.1, "max_tokens": 1500},
                verbose=True
            ),
            cache_mode="BYPASS"
        )

    async def extract_products(self, urls: List[str]):
        results = {}
        crawler = await CrawlerManager.get_crawler() 
        tasks = [self._process_url(crawler, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return {url: result for url, result in zip(urls, results)}

    async def _process_url(self, crawler, url):
        try:
            result = await crawler.arun(url=url, config=self.crawl_config)
            if result.success:
                return json.loads(result.extracted_content)
            return {"error": result.error_message}
        except Exception as e:
            return {"error": str(e)}

extractor = ProductExtractor()

# Usage Example
async def main():
    extractor = ProductExtractor()
    urls = [
        "https://example.com/products/1",
        "https://example.com/products/2"
    ]
    
    results = await extractor.extract_products(urls)
    
    for url, data in results.items():
        print(f"\nResults for {url}:")
        if "error" in data:
            print(f"Error: {data['error']}")
        else:
            product = Product(**data)
            print(f"Name: {product.name}")
            print(f"Price: {product.price}")
            print(f"Description: {product.description[:100]}...")
            print(f"Features: {', '.join(product.features or [])}")
            print(f"Rating: {product.rating or 'N/A'}")
            print(f"Image: {product.image_url or 'N/A'}")

if __name__ == "__main__":
    asyncio.run(main())