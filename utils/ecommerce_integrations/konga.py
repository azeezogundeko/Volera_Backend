from typing import Dict, Any, List, Optional
import aiohttp
from urllib.parse import urlparse, parse_qs
from config import KONGA_API_KEY, KONGA_ID

from ..ecommerce.base import GraphQLIntegration


class KongaIntegration(GraphQLIntegration):
    def __init__(self):
        super().__init__(
            name="konga",
            base_url="https://www.konga.com",
            url_patterns=["konga.com"],
            graphql_url=F"https://{KONGA_ID}-dsn.algolia.net/1/indexes/*/queries",
            queries={},
            headers={
                "X-Algolia-Application-Id": KONGA_ID,
                "X-Algolia-API-Key": KONGA_API_KEY,
                "Content-Type": "application/json",
            }
        )

    def _extract_url_key(self, url: str) -> str:
        """Extract URL key from product URL."""
        # Example: https://www.konga.com/product/some-product-url-key
        path = urlparse(url).path
        if "/product/" in path:
            return path.split("/product/")[-1].strip("/")
        return ""

    def _extract_search_params(self, url: str) -> Dict[str, Any]:
        """Extract search parameters from URL."""
        # Example: https://www.konga.com/search?search=laptop&page=2
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        return {
            "search": params.get("search", [""])[0],
            "page": int(params.get("page", ["1"])[0]) - 1,  # Convert to 0-based index
            "limit": int(params.get("limit", ["40"])[0]),
            "sort": params.get("sort", [""])[0]
        }

    def _transform_algolia_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Algolia response to standard format."""
        products = []
        
        for hit in data.get("hits", []):
            # Get description text from the nested structure
            description = hit.get("description", {}).get("result", "")
            
            products.append({
                "name": hit.get("name", ""),
                "description": description,
                "current_price": str(hit.get("price", 0)),
                "original_price": str(hit.get("price", 0)),  # Use price as original if no special
                "special_price": str(hit.get("special_price", 0)),
                "deal_price": str(hit.get("deal_price", 0)) if hit.get("deal_price") else None,
                "image": f"https://www-konga-com-res.cloudinary.com/w_auto,f_auto,fl_lossy,dpr_auto,q_auto/media/catalog/product{hit.get('image_thumbnail_path', '')}",
                "images": [],  # TODO: Add if available in response
                "url": f"/product/{hit.get('url_key', '')}",
                "source": "konga",
                "product_id": hit.get("objectID", ""),
                "brand": hit.get("brand", ""),
                "sku": hit.get("sku", ""),
                "seller": {
                    "name": hit.get("seller", {}).get("name", ""),
                    "is_premium": bool(hit.get("seller", {}).get("is_premium", 0)),
                    "is_konga": bool(hit.get("seller", {}).get("is_konga", 0)),
                    "city": hit.get("seller", {}).get("city", ""),
                    "state": hit.get("seller", {}).get("state", "")
                },
                "stock": {
                    "in_stock": bool(hit.get("stock", {}).get("in_stock", 0)),
                    "quantity": hit.get("stock", {}).get("quantity", 0),
                    "quantity_sold": hit.get("stock", {}).get("quantity_sold", 0),
                    "min_sale_qty": hit.get("stock", {}).get("min_sale_qty", 1),
                    "max_sale_qty": hit.get("stock", {}).get("max_sale_qty", 0)
                },
                "rating": {
                    "average": hit.get("rating", {}).get("average_rating", 0),
                    "total": hit.get("rating", {}).get("total_rating", 0)
                },
                "is_free_shipping": bool(hit.get("is_free_shipping", 0)),
                "is_pay_on_delivery": bool(hit.get("is_pay_on_delivery", 0)),
                "express_delivery": bool(hit.get("express_delivery", 0)),
                "konga_fulfilment_type": hit.get("konga_fulfilment_type", ""),
                "is_official_store": bool(hit.get("is_official_store_product", 0))
            })
        
        return {
            "products": products,
            "pagination": {
                "page": data.get("page", 0) + 1,  # Convert to 1-based index
                "limit": data.get("hitsPerPage", 40),
                "total": data.get("nbHits", 0),
                "total_pages": data.get("nbPages", 0)
            }
        }

    async def get_product_list(self, url: str, **kwargs) -> Dict[str, Any]:
        """Get product list using Algolia."""
        # Extract search parameters from URL or kwargs
        if "/search" in url:
            params = self._extract_search_params(url)
        else:
            params = {
                "search": kwargs.get("search", ""),
                "page": kwargs.get("page", 0),
                "limit": kwargs.get("limit", 40),
                "sort": kwargs.get("sort", "")
            }

        # Parse search terms for Algolia query
        search_query = params["search"].strip()
        
        # Build Algolia request payload
        payload = {
            "requests": [
                {
                    "indexName": "catalog_store_konga_price_asc",
                    "params": f"query={search_query}&facetFilters=[]&page={params['page']}&hitsPerPage={params['limit']}"
                },
                {
                    "indexName": "catalog_store_konga_price_asc",
                    "params": (
                        f"query={search_query}&"
                        "maxValuesPerFacet=50&"
                        f"page={params['page']}&"
                        "highlightPreTag=<ais-highlight-0000000000>&"
                        "highlightPostTag=</ais-highlight-0000000000>&"
                        "hitsPerPage=1&"
                        "attributesToRetrieve=[]&"
                        "attributesToHighlight=[]&"
                        "attributesToSnippet=[]&"
                        "analytics=false&"
                        "clickAnalytics=false&"
                        "facets=attributes.brand"
                    )
                }
            ]
        }

        print("Algolia payload:", payload)  # Debug print

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.graphql_url,
                        headers=self.headers,
                        json=payload
                ) as response:
                        data = await response.json()
                        if response.status == 200 and "results" in data:
                            # Transform the first result (product list)
                            result = data["results"][0]
                            return self._transform_algolia_response(result)
                        else:
                            print(f"Error response from Algolia API: {data}")

            except Exception as e:
                print(f"Exception during Algolia API request: {str(e)}")
        return {"products": [], "pagination": {"page": 1, "limit": 40, "total": 0, "total_pages": 0}}

    async def get_product_detail(self, url: str, **kwargs) -> Dict[str, Any]:
        """Get product detail using GraphQL."""
        url_key = self._extract_url_key(url)
        if not url_key:
            return {}

        # Update headers with dynamic Referer
        headers = self.headers.copy()
        headers["Referer"] = url

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.graphql_url,
                headers=headers,
                json={
                    "query": self.queries["productDetail"],
                    "variables": {
                        "url_key": url_key
                    }
                }
            ) as response:
                print(response)
                if response.status == 200:
                    data = await response.json()
                    return self._transform_product_detail(data)
                else:
                    error_data = await response.text()
                    print(f"Error response from Konga API: {error_data}")
        return {} 