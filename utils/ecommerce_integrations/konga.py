from typing import Dict, Any, Union
import aiohttp
from urllib.parse import urlparse, parse_qs
from config import KONGA_API_KEY, KONGA_ID

from ..ecommerce.base import GraphQLIntegration
from ..db_manager import ProductDBManager

from ..logging import logger


class KongaIntegration(GraphQLIntegration):
    def __init__(self, db_manager: ProductDBManager = None):
        """
        Initialize KongaIntegration.
        
        Args:
            db_manager: Optional database manager instance for caching
        """
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
        self.db_manager = db_manager

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

    def _clean_rating(self, rating: Union[Dict, float, str, None]) -> float:
        """Clean rating value and convert to float."""
        if not rating:
            return 0.0
        
        # If rating is a dictionary with 'average' key (Konga format)
        if isinstance(rating, dict):
            return float(rating.get('average', 0.0))
        
        # If rating is a string (e.g., "4.5 out of 5")
        if isinstance(rating, str):
            try:
                return float(''.join(filter(lambda x: x.isdigit() or x == '.', rating)))
            except (ValueError, TypeError):
                return 0.0
                
        # If rating is already a float or int
        try:
            return float(rating)
        except (ValueError, TypeError):
            return 0.0

    async def _cache_product(self, product: Dict[str, Any], query_string: str = None, type="list"):
        """Helper method to cache product if db_manager is available."""
        if self.db_manager:
            try:
                await self.db_manager.cache_product(
                    product_id=product["product_id"],
                    data=product,
                    ttl=3600,
                    type=type,
                    query=query_string
                )
            except Exception as e:
                print(f"Error caching product: {str(e)}")

    async def _transform_algolia_response(self, data: Dict[str, Any], search_params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Algolia response to standard format."""
        products = []
        
        for hit in data.get("hits", []):
            # print(hit)
            product = {
                "name": hit.get("name", ""),
                "brand": hit.get("brand", ""),
                "category": self.extract_category(hit.get("name", "")),
                "description": hit.get("description", {}).get("result", ""),
                "current_price": hit.get("price", 0),
                "original_price": hit.get("price", 0),
                "discount": hit.get("discount_percentage", 0),
                "image": f"https://www-konga-com-res.cloudinary.com/w_auto,f_auto,fl_lossy,dpr_auto,q_auto/media/catalog/product{hit.get('image_thumbnail_path', '')}",
                "images": [
                    {
                        "url": f"https://www-konga-com-res.cloudinary.com/w_auto,f_auto,fl_lossy,dpr_auto,q_auto/media/catalog/product{img_path}",
                        "zoom_url": f"https://www-konga-com-res.cloudinary.com/w_auto,f_auto,fl_lossy,dpr_auto,q_auto/media/catalog/product{img_path}",
                        "alt": hit.get("name", "")
                    }
                    for img_path in hit.get("image_paths", [])
                ],
                "source": "konga",
                "rating": self._clean_rating(hit.get("rating", {}).get("average_rating", 0)),
                "rating_count": hit.get("rating", {}).get("count", 0),
                "seller": {
                    "name": hit.get("seller", {}).get("name", ""),
                    "rating": hit.get("seller", {}).get("rating", 0)
                },
                "specifications": [],  # Not available in list view
                "features": [],  # Not available in list view
                "reviews": [],  # Not available in list view
                "product_id": self.hash_id(f"{self.base_url}/product/{hit.get('url_key', '')}"),
                "url": f"{self.base_url}/product/{hit.get('url_key', '')}",
                
                # Additional Konga-specific fields
                "sku": hit.get("sku", ""),
                "stock": {
                    "in_stock": bool(hit.get("stock", {}).get("in_stock", 0)),
                    "quantity": hit.get("stock", {}).get("quantity", 0),
                    "quantity_sold": hit.get("stock", {}).get("quantity_sold", 0),
                    "min_sale_qty": hit.get("stock", {}).get("min_sale_qty", 1),
                    "max_sale_qty": hit.get("stock", {}).get("max_sale_qty", 0)
                },
                "is_free_shipping": bool(hit.get("is_free_shipping", 0)),
                "is_pay_on_delivery": bool(hit.get("is_pay_on_delivery", 0)),
                "express_delivery": bool(hit.get("express_delivery", 0)),
                "konga_fulfilment_type": hit.get("konga_fulfilment_type", ""),
                "is_official_store": bool(hit.get("is_official_store_product", 0))
            }
            
            products.append(product)

            # Cache the product with search parameters if db_manager is available
            if self.db_manager:
                query_string = f"search={search_params['search']}&page={search_params['page']}&limit={search_params['limit']}&sort={search_params['sort']}"
                await self._cache_product(product, query_string, type="list")
        
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
                            return await self._transform_algolia_response(result, params)
                        else:
                            print(f"Error response from Algolia API: {data}")

            except Exception as e:
                logger.error(f"Exception during Algolia API request: {str(e)}", exc_info=True)

        return {"products": [], "pagination": {"page": 1, "limit": 40, "total": 0, "total_pages": 0}}

    async def get_product_detail(self, url: str, product_id: str, **kwargs) -> Dict[str, Any]:
        """Get product detail using GraphQL."""
        if self.db_manager:
            product = await self.db_manager.get_cached_product(product_id, type="list")
            if product:
                return product
        return {}

        