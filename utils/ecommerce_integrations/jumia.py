from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs
from ..ecommerce.base import ScrapingIntegration


class JumiaIntegration(ScrapingIntegration):
    def __init__(self):
        super().__init__(
            name="jumia",
            base_url="https://www.jumia.com.ng",
            url_patterns=["jumia.com.ng"],
            list_schema={
                "name": "Jumia Product List Schema",
                "baseSelector": "article.prd._fb.col.c-prd",
                "fields": [
                    {
                        "name": "name",
                        "selector": ".product-name, .product-title, h2, h3.name, .qa-advert-title",  # Added Jiji's selector
                        "type": "text"
                    },
                    {
                        "name": "current_price",
                        "selector": ".price, .product-price, .current-price, div.prc, .qa-advert-price",  # Added Jiji's selector
                        "type": "text"
                    },
                    {
                        "name": "original_price",
                        "selector": ".original-price, .old-price, .regular-price, .current-price, .old",
                        "type": "text",
                        "optional": True
                    },
                    {
                        "name": "discount",
                        "selector": ".discount, .savings, .price-off, ._dsct",
                        "type": "text",
                        "optional": True
                    },
                    {
                        "name": "url",
                        "selector": "a.core",
                        "type": "attribute",
                        "attribute": "href"
                    },
                    {
                        "name": "image",
                        "selector": "img.img[data-src], img.img[src*='jumia'], img[data-nuxt-pic], img",  # Prioritize data-src for Jumia
                        "type": "attribute",
                        "attribute": "data-src",  # Try data-src first
                        "fallback": {  # Fallback to src if data-src is empty or not found
                            "attribute": "src",
                            "filter": "not_contains:data:image/gif;base64"  # Filter out base64 images
                        }
                    },
                    {
                        "name": "rating",
                        "selector": ".rating, .stars, .product-rating, .stars._s",
                        "type": "text",
                        "optional": True
                    },
                    {
                        "name": "reviews_count",
                        "selector": ".review-count, .rating-count",
                        "type": "text",
                        "optional": True
                    },
                    # {
                    #     "name": "source",
                    #     "default": "jumia"
                    # },
                ]
            },
            detail_schema={
                "name": "Product Detail Schema",
                "baseSelector": "main.-pvs",
                "fields": [
                    {
                        "name": "category",
                        "type": "text",
                        "selector": ".brcbs a.cbs:nth-child(3)"
                    },
                    {
                        "name": "product_basic_info",
                        "selector": "section.col12.-df.-d-co",
                        "type": "nested",
                        "fields": [
                            {
                                "name": "name",
                                "selector": "h1.-fs20.-pts.-pbxs",
                                "type": "text"
                            },
                            {
                                "name": "current_price",
                                "selector": "span.-b.-ubpt.-tal.-fs24.-prxs",
                                "type": "text"
                            },
                            {
                                "name": "original_price",
                                "selector": "span.-tal.-gy5.-lthr.-fs16.-pvxs.-ubpt",
                                "type": "text",
                                "optional": True
                            },
                            {
                                "name": "brand",
                                "selector": "div.-pvxs a:nth-child(1)",
                                "type": "text"
                            },
                            {
                                "name": "discount",
                                "selector": ".bdg._dsct, [data-disc]",
                                "type": "text",
                                "fallback": {
                                    "attribute": "data-disc"
                                },
                                "optional": True
                            },
                            {
                                "name": "rating",
                                "selector": ".stars._m._al",
                                "type": "text",
                                "optional": True
                            },
                            {
                                "name": "reviews_count",
                                "selector": "a._more",
                                "type": "text",
                                "optional": True
                            },
                            {
                                "name": "images",
                                "selector": ".sldr._img._prod a.itm",
                                "type": "list",
                                "fields": [
                                    {
                                        "name": "url",
                                        "selector": "img",
                                        "type": "attribute",
                                        "attribute": "data-src",
                                        "fallback": {
                                            "attribute": "src",
                                            "filter": "not_contains:data:image/gif;base64"
                                        }
                                    },
                                    {
                                        "name": "zoom_url",
                                        "type": "attribute",
                                        "attribute": "href"
                                    },
                                    {
                                        "name": "alt",
                                        "selector": "img",
                                        "type": "attribute",
                                        "attribute": "alt",
                                        "optional": True
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "product_details",
                        "selector": "section.card.aim.-mtm.-fs16",
                        "type": "nested_list",
                        "fields": [
                            {
                                "name": "features",
                                "selector": "div.row.-pas > article:nth-child(1) > div > div > ul > li",
                                "type": "list",
                                "fields": [
                                    {
                                        "name": "feature",
                                        "type": "text",
                                    },
                                ]
                            },
                            {
                                "name": "specifications",
                                "selector": ".card-b:contains('Specifications') ul.-pvs.-mvxs.-phm.-lsn li.-pvxs",
                                "type": "list",
                                "fields": [
                                    {
                                        "name": "value",
                                        "type": "text",
                                    },
                                    {
                                        "name": "label",
                                        "type": "text",
                                        "selector": "span.-b",
                                    },
                                ]
                            },
                        ]
                    },
                    {
                        "name": "product_reviews",
                        "selector": "div.cola.-phm.-df.-d-co",
                        "type": "nested",
                        "fields": [
                            {
                                "name": "reviews",
                                "selector": "article.-pvs.-hr._bet",
                                "type": "list",
                                "fields": [
                                    {
                                        "name": "rating",
                                        "type": "text",
                                        "selector": "div.stars._m._al.-mvs"
                                    },
                                    {
                                        "name": "title",
                                        "type": "text",
                                        "selector": "h3.-m.-fs16.-pvs"
                                    },
                                    {
                                        "name": "comment",
                                        "type": "text",
                                        "selector": "p.-pvs"
                                    },
                                    {
                                        "name": "date",
                                        "type": "text",
                                        "selector": "div.-df.-j-bet.-i-ctr.-gy5 span:first-child"
                                    },
                                    {
                                        "name": "author",
                                        "type": "text",
                                        "selector": "div.-df.-j-bet.-i-ctr.-gy5 span:nth-child(2)"
                                    },
                                    {
                                        "name": "verified",
                                        "type": "boolean",
                                        "selector": "svg.ic.-f-gn5",
                                        "value": True
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )

    def _extract_search_params(self, url: str) -> Dict[str, Any]:
        """Extract search parameters from URL."""
        # Example: https://www.jumia.com.ng/catalog/?q=laptop&page=2
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        return {
            "search": params.get("q", [""])[0],
            "page": int(params.get("page", ["1"])[0]),
            "sort": params.get("sort", [""])[0]
        }

    def _clean_price(self, price: str) -> str:
        """Clean price string."""
        if not price:
            return ""
        # Remove currency symbol and extra spaces
        return price.replace("₦", "").strip()

    def _clean_rating(self, rating: str) -> float:
        """Convert rating string to float."""
        try:
            return float(rating)
        except (ValueError, TypeError):
            return 0.0

    def _clean_rating_count(self, count: str) -> int:
        """Extract rating count from string."""
        if not count:
            return 0
        # Example: "(123 ratings)" -> 123
        try:
            return int(''.join(filter(str.isdigit, count)))
        except ValueError:
            return 0

    def _transform_product_list(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform scraped product list to standard format."""
        transformed = []
        for product in products:
            transformed.append({
                "product_id": self.hash_id(product.get("url", "")),
                "name": product.get("name", ""),
                "current_price": self._clean_price(product.get("current_price", "")),
                "original_price": self._clean_price(product.get("original_price", "")),
                "discount": product.get("discount", ""),
                "image": product.get("image", ""),
                "url": f"{self.base_url}{product.get('url', '')}",
                "source": "jumia",
                "rating": self._clean_rating(product.get("rating", "0")),
                "rating_count": self._clean_rating_count(product.get("rating_count", ""))
            })
        return transformed


    def _transform_product_detail(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform scraped product detail to standard format."""
        return product
        # if not product:
        #     return {}

        # basic_info = product.get("product_basic_info", {})
        # product_details = product.get("product_details", {})
        # product_reviews = product.get("product_reviews", {})

        # return {
        #     "name": basic_info.get("name", ""),
        #     "brand": basic_info.get("brand", ""),
        #     "category": product.get("category", ""),
        #     "description": "",  # Not directly available in schema
        #     "current_price": self._clean_price(basic_info.get("current_price", "")),
        #     "original_price": self._clean_price(basic_info.get("original_price", "")),
        #     "discount": basic_info.get("discount", ""),
        #     "image": basic_info.get("images", [{}])[0].get("url", "") if basic_info.get("images") else "",
        #     "images": [
        #         {
        #             "url": img.get("url", ""),
        #             "zoom_url": img.get("zoom_url", ""),
        #             "alt": img.get("alt", "")
        #         }
        #         for img in basic_info.get("images", [])
        #     ],
        #     "source": "jumia",
        #     "rating": self._clean_rating(basic_info.get("rating", "0")),
        #     "rating_count": self._clean_rating_count(basic_info.get("reviews_count", "")),
        #     "seller": {
        #         "name": "",  # Not available in schema
        #         "rating": 0  # Not available in schema
        #     },
        #     "specifications": [
        #         {
        #             "label": spec.get("label", ""),
        #             "value": spec.get("value", "")
        #         }
        #         for spec in product_details.get("specifications", [])
        #     ],
        #     "features": [
        #         feature.get("feature", "")
        #         for feature in product_details.get("features", [])
        #     ],
        #     "reviews": [
        #         {
        #             "rating": self._clean_rating(review.get("rating", "0")),
        #             "title": review.get("title", ""),
        #             "comment": review.get("comment", ""),
        #             "date": review.get("date", ""),
        #             "author": review.get("author", ""),
        #             "verified": review.get("verified", False)
        #         }
        #         for review in product_reviews.get("reviews", [])
        #     ]
        # }

    async def get_product_list(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """Get product list by scraping."""
        products = await super().get_product_list(url, **kwargs)
        return self._transform_product_list(products)

    async def get_product_detail(self, url: str, **kwargs) -> Dict[str, Any]:
        """Get product detail by scraping."""
        product = await super().get_product_detail(url, **kwargs)
        return self._transform_product_detail(product) 