import hashlib
from typing import Dict, Any, Optional, List, Union, Literal
from datetime import datetime

from pydantic import BaseModel

from .logging import logger
from .ecommerce.base import EcommerceIntegration
from .db_manager import ProductDBManager


class CacheEntry(BaseModel):
    data: Union[Dict[str, Any], List[Dict[str, Any]]]
    timestamp: datetime
    type: Literal["list", "detail"]
    product_id: str
    ttl: Optional[int] = None
    query: Optional[str] = None  # Store original query for similarity check

class EcommerceManager:
    def __init__(self, db_manager: ProductDBManager, similarity_threshold: float = 0.8):
        self._integrations: Dict[str, EcommerceIntegration] = {}
        self.similarity_threshold = similarity_threshold
        self.db_manager = db_manager
        
        # Register default integrations
        self._register_default_integrations()

    def _register_default_integrations(self):
        """Register default website integrations."""
        from .ecommerce_integrations.jumia import JumiaIntegration
        from .ecommerce_integrations.jiji import JijiIntegration
        from .ecommerce_integrations.konga import KongaIntegration
        
        # Register each integration with db_manager
        integrations = [
            JumiaIntegration(db_manager=self.db_manager),
            JijiIntegration(db_manager=self.db_manager),
            KongaIntegration(db_manager=self.db_manager)
        ]
        
        for integration in integrations:
            self.register_integration(integration)

    def register_integration(self, integration: EcommerceIntegration) -> None:
        """Register a new e-commerce integration."""
        self._integrations[integration.name] = integration

    def get_integration_for_url(self, url: str) -> Optional[EcommerceIntegration]:
        """Get the registered integration for a given URL."""
        for integration in self._integrations.values():
            if integration.matches_url(url):
                return integration
        return None

    def generate_product_id(self, url: str) -> str:
        """Generate a unique product ID from a URL."""
        return hashlib.sha256(url.encode()).hexdigest()

    def _preprocess_url(self, url: str) -> str:
        """Preprocess URL before fetching data."""
        if "?" in url and any(integration.matches_url(url) for integration in self._integrations.values()):
            url = url.split("?")[0]
        return url.strip()

    async def process_url(
        self,
        url: str,
        ttl: Optional[int] = 3600,
        bypass_cache: bool = False
    ) -> List[Dict[str, Any]]:
        """Process a single URL and return extracted products."""
        try:
            processed_url = self._preprocess_url(url)
            logger.info(f"Processing URL: {processed_url}")
            
            product_id = self.generate_product_id(processed_url)
            
            # Check cache first
            if not bypass_cache:
                cached = await self.db_manager.get_cached_product(product_id)
                if cached:
                    return cached if isinstance(cached, list) else [cached]
            
            # Get integration
            integration = self.get_integration_for_url(processed_url)
            if not integration:
                logger.warning(f"No integration found for URL: {processed_url}")
                return []
            
            # Get product list
            products = await integration.get_product_list(
                url=processed_url,
                bypass_cache=bypass_cache
            )
            
            if products:
                await self.db_manager.cache_product(
                    product_id=product_id,
                    data=products,
                    ttl=ttl,
                    query=processed_url
                )
            
            return products
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            return []

    async def get_product_detail(
        self,
        product_id: str,
        bypass_cache: bool = False,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get detailed product information from a URL."""
        try:
            # Check cache first if not bypassing
            if not bypass_cache:
                cached_product = await self.db_manager.get_cached_product(product_id, type="detail")
                if cached_product:
                    print("cache_hit")
                    return cached_product

            # Try to get from list cache for the URL
            list_product = await self.db_manager.get_cached_product(product_id, type="list")
            if not list_product:
                logger.error(f"Product {product_id} not found in cache")
                return {}

            product_url = list_product.get("url")
            if not product_url:
                logger.error(f"Product URL not found for {product_id}")
                return {}

            integration = self.get_integration_for_url(product_url)
            if not integration:
                logger.error(f"No integration found for product URL: {product_url}")
                return {}
            
            product = await integration.get_product_detail(
                url=product_url,
                bypass_cache=bypass_cache
            )

            if product:
                await self.db_manager.cache_product(
                    product_id=product_id,
                    data=product,
                    ttl=ttl
                )
                return product
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting product detail for {product_id}: {str(e)}")
            return {}



    # async def rerank_products_by_price(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """Rerank products based on price."""
    #     pass

    # async def rerank_products_by_rating(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """Rerank products based on rating."""
    #     pass

    # async def rerank_products_by_reviews(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """Rerank products based on reviews."""
    #     pass

    # async def rerank_products_by_brand(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """Rerank products based on brand."""
    #     pass

    # async def rerank_products_by_availability(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """Rerank products based on availability."""
    #     pass

    # async def rerank_products_by_seller(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """Rerank products based on seller."""
    #     pass

    # async def rerank_products_by_location(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     """Rerank products based on location."""
    #     pass

 