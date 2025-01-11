from typing import Dict, Any, List, Optional
import aiohttp
from urllib.parse import urlparse, parse_qs

from utils.ecommerce.base import GraphQLIntegration


class KongaIntegration(GraphQLIntegration):
    def __init__(self):
        super().__init__(
            name="konga",
            base_url="https://www.konga.com",
            url_patterns=["konga.com"],
            graphql_url="https://api.konga.com/v1/graphql",
            queries={
                "productList": """
                    query ProductList($search_term: [String], $page: Int!, $limit: Int!, $sortBy: String) {
                        searchByStore(
                            search_term: $search_term,
                            numericFilters: [],
                            sortBy: $sortBy,
                            paginate: {page: $page, limit: $limit},
                            store_id: 1
                        ) {
                            pagination {
                                limit,
                                page,
                                total
                            },
                            products {
                                brand,
                                deal_price,
                                description,
                                final_price,
                                image_thumbnail,
                                image_thumbnail_path,
                                image_full,
                                images,
                                name,
                                objectID,
                                original_price,
                                product_id,
                                product_type,
                                price,
                                status,
                                special_price,
                                sku,
                                url_key,
                                seller {
                                    id,
                                    name,
                                    url,
                                    is_premium,
                                    is_konga
                                },
                                stock {
                                    in_stock,
                                    quantity,
                                    quantity_sold
                                }
                            }
                        }
                    }
                """,
                "productDetail": """
                    query ProductDetail($url_key: String!) {
                        product(url_key: $url_key) {
                            brand,
                            deal_price,
                            description,
                            final_price,
                            image_full,
                            images,
                            name,
                            objectID,
                            original_price,
                            product_id,
                            product_type,
                            price,
                            status,
                            special_price,
                            sku,
                            seller {
                                id,
                                name,
                                url,
                                is_premium,
                                is_konga,
                                ratings {
                                    quality {
                                        average,
                                        number_of_ratings
                                    }
                                }
                            },
                            stock {
                                in_stock,
                                quantity,
                                quantity_sold
                            },
                            variants {
                                attributes {
                                    id,
                                    code,
                                    label,
                                    options {
                                        id,
                                        code,
                                        value
                                    }
                                }
                            }
                        }
                    }
                """
            },
            headers={
                ":authority": "api.konga.com",
                ":method": "POST",
                ":path": "/v1/graphql",
                ":scheme": "https",
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json",
                "origin": "https://www.konga.com",
                "priority": "u=1, i",
                "referer": "https://www.konga.com/",
                "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "x-app-source": "kongavthree",
                "x-app-version": "2.0"
            }
        )

    def _extract_url_key(self, url: str) -> str:
        """Extract URL key from product URL."""
        # Example: https://www.konga.com/product/some-product-url-key
        path = urlparse(url).path
        if "/product/" in path:
            return path.split("/product/")[-1].strip("/")
        return ""

    def _transform_product_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform GraphQL response to standard format."""
        products = []
        for product in data.get("data", {}).get("searchByStore", {}).get("products", []):
            products.append({
                "name": product.get("name", ""),
                "description": product.get("description", ""),
                "current_price": str(product.get("final_price", "")),
                "original_price": str(product.get("original_price", "")),
                "image": product.get("image_full", ""),
                "images": product.get("images", []),
                "url": f"/product/{product.get('url_key', '')}",
                "source": "konga",
                "product_id": product.get("product_id", ""),
                "seller": {
                    "name": product.get("seller", {}).get("name", ""),
                    "is_premium": product.get("seller", {}).get("is_premium", False),
                    "is_konga": product.get("seller", {}).get("is_konga", False)
                },
                "stock": {
                    "in_stock": product.get("stock", {}).get("in_stock", False),
                    "quantity": product.get("stock", {}).get("quantity", 0)
                }
            })
        return products

    def _transform_product_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform GraphQL response to standard format."""
        product = data.get("data", {}).get("product", {})
        if not product:
            return {}

        seller = product.get("seller", {})
        seller_ratings = seller.get("ratings", {}).get("quality", {})
        
        return {
            "name": product.get("name", ""),
            "description": product.get("description", ""),
            "current_price": str(product.get("final_price", "")),
            "original_price": str(product.get("original_price", "")),
            "special_price": str(product.get("special_price", "")),
            "deal_price": str(product.get("deal_price", "")),
            "image": product.get("image_full", ""),
            "images": product.get("images", []),
            "source": "konga",
            "product_id": product.get("product_id", ""),
            "brand": product.get("brand", ""),
            "sku": product.get("sku", ""),
            "seller": {
                "name": seller.get("name", ""),
                "is_premium": seller.get("is_premium", False),
                "is_konga": seller.get("is_konga", False),
                "rating": {
                    "average": seller_ratings.get("average", 0),
                    "count": seller_ratings.get("number_of_ratings", 0)
                }
            },
            "stock": {
                "in_stock": product.get("stock", {}).get("in_stock", False),
                "quantity": product.get("stock", {}).get("quantity", 0),
                "quantity_sold": product.get("stock", {}).get("quantity_sold", 0)
            },
            "variants": [
                {
                    "id": attr.get("id"),
                    "code": attr.get("code"),
                    "label": attr.get("label"),
                    "options": [
                        {
                            "id": opt.get("id"),
                            "code": opt.get("code"),
                            "value": opt.get("value")
                        }
                        for opt in attr.get("options", [])
                    ]
                }
                for attr in product.get("variants", {}).get("attributes", [])
            ]
        }

    async def get_product_list(self, url: str, **kwargs) -> Dict[str, Any]:
        """Get product list using GraphQL."""
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

        # Convert search term to nested array format as required by Konga's API
        # Example: "phone case" -> [["phone", "case"]]
        search_terms = [[term.strip() for term in params["search"].split()]] if params["search"] else [[]]

        # Update headers with dynamic Referer
        headers = self.headers.copy()
        headers["Referer"] = url

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.graphql_url,
                headers=headers,
                json={
                    "query": self.queries["productList"],
                    "variables": {
                        "search_term": search_terms,
                        "page": params["page"],
                        "limit": params["limit"],
                        "sortBy": params["sort"]
                    }
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_product_list(data)
                else:
                    error_data = await response.text()
                    print(f"Error response from Konga API: {error_data}")
        return {"products": [], "pagination": {"page": 1, "limit": 40, "total": 0, "total_pages": 0}}

    async def get_product_detail(self, url: str, product_id: str, **kwargs) -> Dict[str, Any]:
        """Get product detail using GraphQL."""
        url_key = self._extract_url_key(url)
        if not url_key:
            return {}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.graphql_url,
                headers=self.headers,
                json={
                    "query": self.queries["productDetail"],
                    "variables": {
                        "url_key": url_key
                    }
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_product_detail(data)
        return {}


