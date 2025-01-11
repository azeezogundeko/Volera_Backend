from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs

from ..ecommerce.base import ScrapingIntegration
from ..db_manager import ProductDBManager

class JijiIntegration(ScrapingIntegration):
    def __init__(self, db_manager: ProductDBManager = None):
        super().__init__(
            name="jiji",
            base_url="https://jiji.ng",
            url_patterns=["jiji.ng"],
            list_schema={
                "name": "Jiji Product List Schema",
                "baseSelector": ".b-list-advert__gallery__item",
                "fields": [
                    {
                        "name": "name",
                        "selector": ".qa-advert-title",
                        "type": "text"
                    },
                    {
                        "name": "current_price",
                        "selector": "div.qa-advert-price",
                        "type": "text"
                    },
                    {
                        "name": "url",
                        "selector": "a.b-list-advert-base",
                        "type": "attribute",
                        "attribute": "href"
                    },
                    {
                        "name": "image",
                        "selector": "picture img",  # Updated to target the actual image element
                        "type": "attribute",
                        "attribute": "src",
                        "fallback": {
                            "attribute": "srcset",
                            "filter": "not_contains:data:image/gif;base64"
                        }
                    },
                    {
                        "name": "location",
                        "selector": ".b-list-advert__region__text",
                        "type": "text",
                        "optional": True
                    },
                    {
                    "name": "description",
                    "selector": ".b-list-advert-base__description-text",  # Added Jiji's description
                    "type": "text",
                    "optional": True
                 },
                ]
            },
            detail_schema={
                "name": "Jiji Product Detail Schema",
                "baseSelector": ".b-advert-seller-info-wrapper",
                "fields": [
                    {
                        "name": "product_basic_info",
                        "selector": ".b-advert-seller-info-wrapper",
                        "type": "nested",
                        "fields": [
                            {
                                "name": "name",
                                "selector": ".b-advert-title-inner.qa-advert-title",
                                "type": "text"
                            },
                            {
                                "name": "current_price",
                                "selector": "span.qa-advert-price-view-value",
                                "type": "text"
                            },
                            {
                                "name": "images",
                                "selector": ".VueCarousel-inner .VueCarousel-slide",  # Target all slides in carousel
                                "type": "list",
                                "fields": [
                                    {
                                        "name": "url",
                                        "selector": "picture source",  # Target the webp source
                                        "type": "attribute",
                                        "attribute": "srcset"
                                    },
                                    {
                                        "name": "alt",
                                        "selector": "img.b-slider-image.qa-carousel-slide",
                                        "type": "attribute",
                                        "attribute": "alt",
                                        "optional": True
                                    },   
                                ]
                            },
                        ]
                    },
                    # {
                    #     "name": "seller",
                    #     "type": "nested",
                    #     "fields": [
                    #         {
                    #             "name": "name",
                    #             "selector": "div.b-advert-user-info__name",
                    #             "type": "text"
                    #         },
                    #         {
                    #             "name": "verified",
                    #             "selector": "div.b-advert-user-info i.verified-business-icon",
                    #             "type": "exists",
                    #             "optional": True
                    #         },
                    #         {
                    #             "name": "member_since",
                    #             "selector": "div.b-advert-user-info__date",
                    #             "type": "text",
                    #             "optional": True
                    #         },
                    #         {
                    #             "name": "phone",
                    #             "selector": "div.b-advert-user-info__phone",
                    #             "type": "text",
                    #             "optional": True
                    #         }
                    #     ]
                    # },
                    
                    {
                    "name": "specifications",
                    "selector": ".b-advert-attribute",
                    "type": "list",
                    "fields": [
                        {
                            "name": "key",
                            "selector": ".b-advert-attribute__key",
                            "type": "text"
                        },
                        {
                            "name": "value",
                            "selector": ".b-advert-attribute__value",
                            "type": "text"
                        }
                    ]
                },
                {
                        "name": "description",
                        "selector": ".qa-description-text",
                        "type": "text"
                    },
                ]
            }
        )
        self.db_manager = db_manager
        
    
    def _extract_search_params(self, url: str) -> Dict[str, Any]:
        """Extract search parameters from URL."""
        # Example: https://jiji.ng/search?query=laptop&page=2
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        return {
            "search": params.get("query", [""])[0],
            "page": int(params.get("page", ["1"])[0]),
            "sort": params.get("sort", [""])[0]
        }

    def _clean_price(self, price: str) -> float:
        """Clean price string and convert to float."""
        if not price:
            return 0.0
        # Remove currency symbol (₦), commas, and extra spaces
        cleaned = price.replace("₦", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            print(f"Error converting price to float: {price}")
            return 0.0

    def _clean_discount(self, discount: str) -> float:
        """Convert discount string to float percentage."""
        if not discount:
            return 0.0
        # Extract number from strings like "-25%" or "25% OFF"
        cleaned = ''.join(filter(str.isdigit, discount))
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            print(f"Error converting discount to float: {discount}")
            return 0.0

    def _clean_date(self, date: str) -> str:
        """Clean date string."""
        if not date:
            return ""
        return date.replace("Member since ", "").strip()


    def _clean_features(self, v):
        if isinstance(v, list):
            print(v)
            return [feature["feature"] for feature in v if isinstance(feature, dict)]
        return v


    
    async def _transform_product_list(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform scraped product list to standard format."""
        # print(products)
        # print("\n\n\n")
        transformed = []
        for product in products:
            transformed.append({
                "name": product.get("name", ""),
                "product_id": self.hash_id(product.get("url", "")),
                "current_price": self._clean_price(product.get("current_price", "")),
                "original_price": self._clean_price(product.get("original_price", "")),
                "discount": self._clean_discount(product.get("discount", "")),
                "image": product.get("image", ""),
                "url": f"{self.base_url}{product.get("url", "")}",
                "source": "jiji",
                "location": product.get("location", ""),
                "seller": {
                    "name": product.get("seller", {}).get("name", ""),
                    "verified": product.get("seller", {}).get("verified", False)
                }
            })

            await self.db_manager.cache_product(
                product_id=self.hash_id(product.get("url", "")),
                data=transformed,
                type="list",
                ttl=3600,
            )
           
        return transformed

    async def _transform_product_detail(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform scraped product detail to standard format."""


        product["source"] = self.name
        product_id = self.hash_id(product["url"])

        product_data = await self.db_manager.get_cached_product(product_id, type="list")
        if product_data:
            product["product_id"] = product_data["product_id"]
            product["current_price"] = product_data["current_price"]
            product["original_price"] = product_data["original_price"]
            product["discount"] = product_data["discount"]
            product["image"] = product_data["image"]
            product["url"] = product_data["url"]
        return product

    async def get_product_list(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """Get product list by scraping."""
        products = await super().get_product_list(url, **kwargs)
        return await self._transform_product_list(products)

    async def get_product_detail(self, url: str, **kwargs) -> Dict[str, Any]:
        """Get product detail by scraping."""
        product = await super().get_product_detail(url, **kwargs)
        return await self._transform_product_detail(product) 