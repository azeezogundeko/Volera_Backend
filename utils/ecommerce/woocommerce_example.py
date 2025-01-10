from typing import Dict, Any, List
import aiohttp
from urllib.parse import urlparse, parse_qs
from .base import RestApiIntegration

class WooCommerceIntegration(RestApiIntegration):
    def __init__(self):
        # These would typically come from configuration
        super().__init__(
            name="woocommerce_store",
            base_url="https://your-store.com",
            url_patterns=["your-store.com"],
            api_base_url="https://your-store.com/wp-json/wc/v3",
            api_key="your_consumer_key",
            headers={
                "Accept": "application/json"
            }
        )

    def _extract_product_id(self, url: str) -> str:
        """Extract product ID from URL."""
        # Example URL: https://your-store.com/product/product-slug-123
        path = urlparse(url).path
        if "/product/" in path:
            # Extract ID from slug (assuming format: slug-{id})
            slug = path.split("/product/")[-1].strip("/")
            return slug.split("-")[-1]
        return ""

    def _extract_category_id(self, url: str) -> str:
        """Extract category ID from URL."""
        # Example URL: https://your-store.com/product-category/category-slug
        path = urlparse(url).path
        if "/product-category/" in path:
            return path.split("/product-category/")[-1].strip("/")
        return ""

    def _transform_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform WooCommerce product to standard format."""
        return {
            "name": product.get("name", ""),
            "description": product.get("description", ""),
            "current_price": product.get("price", ""),
            "original_price": product.get("regular_price", ""),
            "image": product.get("images", [{}])[0].get("src", ""),
            "images": [img.get("src", "") for img in product.get("images", [])],
            "url": product.get("permalink", ""),
            "source": "woocommerce_store",
            "categories": [
                cat.get("name", "") for cat in product.get("categories", [])
            ],
            "tags": [
                tag.get("name", "") for tag in product.get("tags", [])
            ],
            "variants": [
                {
                    "id": var.get("id"),
                    "name": var.get("name"),
                    "price": var.get("price"),
                    "stock_status": var.get("stock_status")
                }
                for var in product.get("variations", [])
            ]
        }

    async def get_product_list(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """Get product list using WooCommerce REST API."""
        params = {
            "per_page": kwargs.get("per_page", 20)
        }
        
        # Handle category pages
        category_id = self._extract_category_id(url)
        if category_id:
            params["category"] = category_id
            
        # Handle search
        search_query = kwargs.get("search_query")
        if search_query:
            params["search"] = search_query

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base_url}/products",
                headers=self.headers,
                params=params
            ) as response:
                if response.status == 200:
                    products = await response.json()
                    return [self._transform_product(p) for p in products]
        return []

    async def get_product_detail(self, url: str, **kwargs) -> Dict[str, Any]:
        """Get product detail using WooCommerce REST API."""
        product_id = self._extract_product_id(url)
        if not product_id:
            return {}

        async with aiohttp.ClientSession() as session:
            # Get main product data
            async with session.get(
                f"{self.api_base_url}/products/{product_id}",
                headers=self.headers
            ) as response:
                if response.status != 200:
                    return {}
                    
                product = await response.json()
                
                # Get variations if any
                if product.get("type") == "variable":
                    async with session.get(
                        f"{self.api_base_url}/products/{product_id}/variations",
                        headers=self.headers
                    ) as var_response:
                        if var_response.status == 200:
                            product["variations"] = await var_response.json()
                
                return self._transform_product(product)
        return {} 