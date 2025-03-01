from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Literal
from enum import Enum

from utils.url_shortener import URLShortener
from ..request_session import http_client
from ..scrape import TrackerWebScraper
from ..entity_recognition import extract_brands, extract_categories

from utils.logging import logger



class IntegrationType(Enum):
    SCRAPING = "scraping"
    REST_API = "rest_api"
    GRAPHQL = "graphql"


class EcommerceIntegration(ABC):
    """Base class for all e-commerce integrations."""
    
    def __init__(
        self,
        name: str,
        base_url: str,
        url_patterns: List[str],
        integration_type: Literal["scraping", "api", "graphql"] = "scraping"
    ):
        self.name = name
        self.scraper = TrackerWebScraper()
        self.url_shortner = URLShortener()
        self.base_url = base_url
        self.url_patterns = url_patterns
        self.integration_type = integration_type

        # # Initialize entity recognition once
        # if not hasattr(self, 'entity_recognition'):
        #     self.entity_recognition = prepare_entity_recognition()

    def extract_brands(self, doc):
        return extract_brands(doc)

    def extract_category(self, doc):
        return extract_categories(doc)

    @abstractmethod
    async def get_product_list(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """Get list of products from a category/search page."""
        pass

    async def get_product_detail(self, url: str, **kwargs) -> Dict[str, Any]:
        """Get details for a specific product"""
        pass    

    def matches_url(self, url: str) -> bool:
        """Check if URL matches this integration's patterns."""
        return any(pattern in url for pattern in self.url_patterns)

    def generate_url_id(self, text: str) -> str:
        return self.url_shortner.shorten_url(text)

    def get_full_url(self, short_code: str) -> str:
        return self.url_shortner.enlarge_url(short_code)
        

class ScrapingIntegration(EcommerceIntegration):
    """Integration for websites that require scraping."""
    
    def __init__(
        self,
        name: str,
        base_url: str,
        url_patterns: List[str],
        list_schema: Dict[str, Any],
        detail_schema: Dict[str, Any]
    ):
        super().__init__(name, base_url, url_patterns, "scraping")
        self.list_schema = list_schema
        self.detail_schema = detail_schema
        self.client = http_client

    async def get_product_list(self, url: str, custom_headers: dict = {}, use_flare_bypasser: bool = False, **kwargs) -> List[Dict[str, Any]]:
        from utils._craw4ai import extract_data_with_css
        products = await extract_data_with_css(
            url=url,
            schema=self.list_schema,
            bypass_cache=kwargs.pop('bypass_cache', False),
            custom_headers=custom_headers,
            page_timeout=kwargs.pop('page_timeout', 30000),
            use_flare_bypasser=use_flare_bypasser,
            **kwargs
        )
        return products if isinstance(products, list) else [products] if products else []

    async def get_product_detail(self, url: str, custom_headers: dict = {}, use_flare_bypasser: bool = False, **kwargs) -> Dict[str, Any]:
        from utils._craw4ai import extract_data_with_css
        
    
        try:
            product = await extract_data_with_css(
            url=url,
            schema=self.detail_schema,
            bypass_cache=kwargs.pop('bypass_cache', False),
            custom_headers=custom_headers,
            **kwargs
            )
            
            # Handle different return types safely
            if not product:
                return {}
            
            if isinstance(product, list):
                return product[0] if product else {}
                
            return product
            
        except Exception as e:
            logger.error(f"Error getting product detail from base class: {str(e)}")
            return {}


    async def extract_list_data(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        ""

class RestApiIntegration(EcommerceIntegration):
    """Integration for websites that provide REST APIs."""
    
    def __init__(
        self,
        name: str,
        base_url: str,
        url_patterns: List[str],
        api_base_url: str,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(name, base_url, url_patterns, "api")
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.headers = headers or {}
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    @abstractmethod
    async def get_product_list(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """Implement REST API call for product list."""
        pass

    @abstractmethod
    async def get_product_detail(self, url: str, **kwargs) -> Dict[str, Any]:
        """Implement REST API call for product detail."""
        pass

class GraphQLIntegration(EcommerceIntegration):
    """Integration for websites that use GraphQL."""
    
    def __init__(
        self,
        name: str,
        base_url: str,
        url_patterns: List[str],
        graphql_url: str,
        queries: Dict[str, str],
        headers: Dict[str, str] = None
    ):
        super().__init__(
            name=name,
            base_url=base_url,
            url_patterns=url_patterns,
            integration_type="graphql"
        )
        self.graphql_url = graphql_url
        self.queries = queries
        self.headers = headers or {}

    @abstractmethod
    async def get_product_list(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """Implement GraphQL query for product list."""
        pass

    @abstractmethod
    async def get_product_detail(self, url: str, **kwargs) -> Dict[str, Any]:
        """Implement GraphQL query for product detail."""
        pass 