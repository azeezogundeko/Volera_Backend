from typing import Dict, Any, List
import aiohttp
from .base import GraphQLIntegration

class ShopifyIntegration(GraphQLIntegration):
    def __init__(self):
        # These would typically come from configuration
        super().__init__(
            name="shopify_store",
            base_url="https://your-store.myshopify.com",
            url_patterns=["your-store.myshopify.com"],
            graphql_url="https://your-store.myshopify.com/api/graphql",
            queries={
                "productList": """
                    query ProductList($first: Int!, $query: String) {
                        products(first: $first, query: $query) {
                            edges {
                                node {
                                    id
                                    title
                                    description
                                    priceRange {
                                        minVariantPrice {
                                            amount
                                            currencyCode
                                        }
                                    }
                                    images(first: 1) {
                                        edges {
                                            node {
                                                url
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                """,
                "productDetail": """
                    query ProductDetail($handle: String!) {
                        productByHandle(handle: $handle) {
                            id
                            title
                            description
                            priceRange {
                                minVariantPrice {
                                    amount
                                    currencyCode
                                }
                            }
                            images(first: 10) {
                                edges {
                                    node {
                                        url
                                    }
                                }
                            }
                            variants(first: 10) {
                                edges {
                                    node {
                                        id
                                        title
                                        price
                                        availableForSale
                                    }
                                }
                            }
                        }
                    }
                """
            },
            api_key="your_shopify_storefront_access_token"
        )

    def _extract_handle_from_url(self, url: str) -> str:
        """Extract product handle from URL."""
        # Example URL: https://your-store.myshopify.com/products/product-handle
        return url.split("/products/")[-1].split("?")[0]

    def _transform_product_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform GraphQL response to standard format."""
        products = []
        for edge in data.get("data", {}).get("products", {}).get("edges", []):
            node = edge.get("node", {})
            price_range = node.get("priceRange", {}).get("minVariantPrice", {})
            image = (
                node.get("images", {})
                .get("edges", [{}])[0]
                .get("node", {})
                .get("url", "")
            )
            
            products.append({
                "name": node.get("title", ""),
                "description": node.get("description", ""),
                "current_price": f"{price_range.get('amount')} {price_range.get('currencyCode')}",
                "image": image,
                "url": f"/products/{node.get('handle')}",
                "source": "shopify_store"
            })
        
        return products

    def _transform_product_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform GraphQL response to standard format."""
        product = data.get("data", {}).get("productByHandle", {})
        if not product:
            return {}
            
        price_range = product.get("priceRange", {}).get("minVariantPrice", {})
        images = [
            edge.get("node", {}).get("url")
            for edge in product.get("images", {}).get("edges", [])
        ]
        variants = [
            {
                "id": edge.get("node", {}).get("id"),
                "title": edge.get("node", {}).get("title"),
                "price": edge.get("node", {}).get("price"),
                "available": edge.get("node", {}).get("availableForSale")
            }
            for edge in product.get("variants", {}).get("edges", [])
        ]
        
        return {
            "name": product.get("title", ""),
            "description": product.get("description", ""),
            "current_price": f"{price_range.get('amount')} {price_range.get('currencyCode')}",
            "images": images,
            "variants": variants,
            "source": "shopify_store"
        }

    async def get_product_list(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """Get product list using GraphQL."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.graphql_url,
                headers=self.headers,
                json={
                    "query": self.queries["productList"],
                    "variables": {
                        "first": 20,  # Adjust based on needs
                        "query": kwargs.get("search_query", "")
                    }
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_product_list(data)
        return []

    async def get_product_detail(self, url: str, **kwargs) -> Dict[str, Any]:
        """Get product detail using GraphQL."""
        handle = self._extract_handle_from_url(url)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.graphql_url,
                headers=self.headers,
                json={
                    "query": self.queries["productDetail"],
                    "variables": {
                        "handle": handle
                    }
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_product_detail(data)
        return {} 