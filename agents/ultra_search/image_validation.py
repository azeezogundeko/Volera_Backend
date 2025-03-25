import asyncio
from typing import Dict, Any, List
import aiohttp
from urllib.parse import urljoin, urlparse

from ..legacy.base import BaseAgent
from ..config import agent_manager
from ..state import State
from .schema import ImageValidationSchema
from .prompt import image_validation_prompt
from utils._craw4ai import CrawlerManager
from utils.logging import logger
from schema import ScrapingDependencies
from langgraph.types import Command, Literal
from crawl4ai import CrawlerRunConfig, DefaultMarkdownGenerator

class ImageValidationAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            model='google-gla:gemini-2.0-flash-exp',
            result_type=ImageValidationSchema,
            system_prompt=image_validation_prompt,
            name=agent_manager.image_validation_agent
        )
        self.crawler_config = self.get_crawler_config()

    def get_crawler_config(self):
        """Get crawler configuration optimized for image extraction"""
        md_generator = DefaultMarkdownGenerator()
        config = CrawlerRunConfig(
            excluded_tags=["nav", "footer", "header", "script", "style"],
            exclude_external_links=True,
            markdown_generator=md_generator,
            magic=True,
            bypass_cache=True
        )
        return config

    async def validate_image_url(self, url: str) -> bool:
        """Check if an image URL is valid by making a HEAD request"""
        if not url:
            return False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, allow_redirects=True, timeout=10) as response:
                    content_type = response.headers.get('content-type', '')
                    return response.status == 200 and content_type.startswith('image/')
        except:
            return False

    async def fix_image_url(self, product: Dict) -> str:
        """Attempt to fix an invalid image URL by crawling the product page"""
        try:
            crawler = await CrawlerManager.get_crawler()
            
            # Crawl the product page
            results = await crawler.arun(product['url'], config=self.crawler_config)
            
            # Extract markdown content
            markdown = results.markdown
            if not markdown:
                return product.get('image', '')

            # Use LLM to extract the correct image URL
            prompt = {
                "Task": "Extract the main product image URL from this page",
                "Product Name": product.get('name', ''),
                "Source": product.get('source', ''),
                "Page Content": markdown,
                "Original Image URL": product.get('image', ''),
                "Page URL": product['url']
            }

            response = await self.call_llm(
                user_id="system",  # Since this is an internal operation
                user_prompt=str(prompt),
                type="text",
                model='google-gla:gemini-2.0-flash-exp',
                deps=ScrapingDependencies
            )

            # Extract the image URL from the LLM response
            if response and response.data and response.data.get('image_url'):
                new_image_url = response.data['image_url']
                # Make sure the URL is absolute
                if not bool(urlparse(new_image_url).netloc):
                    new_image_url = urljoin(product['url'], new_image_url)
                return new_image_url
            
            return product.get('image', '')
        except Exception as e:
            logger.error(f"Error fixing image URL: {str(e)}")
            return product.get('image', '')

    async def run(self, state: State, config: Dict[str, Any]) -> ImageValidationSchema:
        """Validate and fix image URLs for all products"""
        research_agent_results = state['agent_results'][agent_manager.summary_agent]
        all_products = research_agent_results.get("all_products", [])
        
        if not all_products:
            return ImageValidationSchema(
                validated_product_ids=[],
                fixed_count=0,
                failed_count=0,
                comment="No products to validate"
            )

        fixed_count = 0
        failed_count = 0
        validated_product_ids = []

        # Create a semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(5)

        async def process_product(product: Dict):
            async with semaphore:
                try:
                    is_valid = await self.validate_image_url(product.get('image', ''))
                    
                    if not is_valid:
                        # Try to fix the image URL
                        new_image_url = await self.fix_image_url(product)
                        is_valid = await self.validate_image_url(new_image_url)
                        
                        if is_valid:
                            nonlocal fixed_count
                            fixed_count += 1
                            product['image'] = new_image_url
                        else:
                            nonlocal failed_count
                            failed_count += 1
                    
                    if is_valid:
                        return product.get('product_id')  # Return only the product ID if validation succeeded
                    return None
                except Exception as e:
                    logger.error(f"Error processing product: {str(e)}")
                    return None

        # Process all products concurrently
        tasks = [process_product(product) for product in all_products]
        results = await asyncio.gather(*tasks)
        
        # Filter out None values and collect valid product IDs
        validated_product_ids = [pid for pid in results if pid is not None]

        comment = f"Validated {len(all_products)} products. Fixed {fixed_count} image URLs. Failed to fix {failed_count} URLs."
        
        await self.websocket_manager.send_progress(
            state['ws_id'],
            status="comment",
            comment=f"Image Validation Agent: {comment}"
        )

        return ImageValidationSchema(
            validated_product_ids=validated_product_ids,
            fixed_count=fixed_count,
            failed_count=failed_count,
            comment=comment
        )

    async def __call__(self, state: State, config: Dict[str, Any] = {}) -> Command[str]:
        """Execute the image validation agent"""
        try:
            result = await self.run(state, config)
            
            # Continue to the next agent in the chain
            all_products = state['agent_results'][agent_manager.summary_agent].get("all_products", [])
            summary_agent_results = state['agent_results'][agent_manager.summary_agent]['content']

            validated_products = [product for product in all_products if product['product_id'] in result.validated_product_ids]
            await self.send_signals(state, content=summary_agent_results['response'], products=validated_products)
            return Command(goto=agent_manager.end, update=state)
        except Exception as e:
            logger.error(f"Image validation failed: {str(e)}", exc_info=True)
            # On error, still try to continue the chain
            return Command(goto=agent_manager.end, update=state)

image_validation_agent = ImageValidationAgent() 