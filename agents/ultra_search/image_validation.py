import asyncio
from typing import Dict, Any, List
import aiohttp
from urllib.parse import urljoin, urlparse

from ..legacy.base import BaseAgent
from ..config import agent_manager
from ..state import State
from .schema import ImageValidationSchema, ProductImage
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
                user_id="system",
                user_prompt=str(prompt),
                type="text",
                model='google-gla:gemini-2.0-flash-exp',
                deps=ScrapingDependencies
            )
            
            return response.image_url if response else ''
        except Exception as e:
            logger.error(f"Error fixing image URL: {str(e)}")
            return product.get('image', '')

    async def run(self, state: State, config: Dict[str, Any]) -> ImageValidationSchema:
        """Validate and fix image URLs for all products"""
        research_agent_results = state['agent_results'][agent_manager.summary_agent]
        all_products = research_agent_results.get("all_products", [])
        
        if not all_products:
            return ImageValidationSchema(
                products=[],
                comment="No products to validate"
            )

        # Create a semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(5)

        async def process_product(product: Dict):
            async with semaphore:
                try:
                    image_url = product.get('image', '')
                    is_valid = await self.validate_image_url(image_url)
                    
                    if not is_valid:
                        # Try to fix the image URL
                        fixed_url = await self.fix_image_url(product)
                        if fixed_url:
                            image_url = fixed_url
                            is_valid = await self.validate_image_url(image_url)
                    
                    if is_valid:
                        # Update the product's image URL directly
                        product['image'] = image_url
                        return ProductImage(
                            image_url=image_url,
                            product_id=product.get('product_id', '')
                        )
                    return None
                except Exception as e:
                    logger.error(f"Error processing product: {str(e)}")
                    return None

        # Process all products concurrently
        tasks = [process_product(product) for product in all_products]
        results = await asyncio.gather(*tasks)
        
        # Filter out None values and collect valid products
        validated_products = [product for product in results if product is not None]

        comment = f"Validated {len(validated_products)} out of {len(all_products)} products."
        
        await self.websocket_manager.send_progress(
            state['ws_id'],
            status="comment",
            comment=f"Image Validation Agent: {comment}"
        )

        return ImageValidationSchema(
            products=validated_products,
            comment=comment
        )

    async def __call__(self, state: State, config: Dict[str, Any] = {}) -> Command[str]:
        """Execute the image validation agent"""
        try:
            result = await self.run(state, config)
            
            # Safely get state data with defaults
            agent_results = state.get('agent_results', {})
            summary_results = agent_results.get(agent_manager.summary_agent, {})
            all_products = summary_results.get("all_products", [])
            content = summary_results.get('content', {})
            
            if not all_products:
                logger.warning("No products found in state")
                return Command(goto=agent_manager.end, update=state)

            # Create a mapping of product IDs to validated image URLs
            validated_images = {p.product_id: p.image_url for p in result.products}
            
            # Update product images in the state
            for product in all_products:
                product_id = product.get('product_id')
                if product_id in validated_images:
                    product['image'] = validated_images[product_id]
            
            # Update the state with validated products
            if agent_manager.summary_agent in agent_results:
                agent_results[agent_manager.summary_agent]['all_products'] = all_products
            
            await self.send_signals(
                state, 
                content=content.get('response', ''),
                products=all_products
            )
            return Command(goto=agent_manager.end, update=state)
        except Exception as e:
            logger.error(f"Image validation failed: {str(e)}", exc_info=True)
            return Command(goto=agent_manager.end, update=state)

image_validation_agent = ImageValidationAgent() 