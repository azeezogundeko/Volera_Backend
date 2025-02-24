import json
from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs

from ..ecommerce.base import ScrapingIntegration
# from ..db_manager import ProductDBManager
from db.cache.dict import DiskCacheDB
from bs4 import BeautifulSoup

class JijiIntegration(ScrapingIntegration):
    def __init__(self, db_manager: DiskCacheDB = None):
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
            url = f"{self.base_url}{product.get('url', '')}"
            product_id = self.generate_url_id(url)
            p = {
                "name": product.get("name", ""),
                "product_id": product_id,
                "category": self.extract_category(product.get("name", "")),
                "brand": self.extract_brands(product.get("name", "")),
                "current_price": self._clean_price(product.get("current_price", "")),
                "original_price": self._clean_price(product.get("original_price", "")),
                "discount": self._clean_discount(product.get("discount", "")),
                "image": product.get("image", ""),
                "url": url,
                "source": "jiji",
                "location": product.get("location", ""),
                "seller": {
                    "name": product.get("seller", {}).get("name", ""),
                    "verified": product.get("seller", {}).get("verified", False)
                }
            }
            # print(url)
            transformed.append(p)

            await self.db_manager.set(
                key=product_id,
                value=p,
                tag="list",
            )
           
        return transformed

    def _validate_nested_structure(self, data: Any) -> Dict[str, Any]:
        """Validate and normalize nested dictionary structure."""
        if not data:
            return {}
        
        if isinstance(data, list):
            if not data:  # Empty list
                return {}
            data = data[0] if isinstance(data[0], dict) else {}
            
        if isinstance(data, dict):
            return data
            
        return {}

    async def _transform_product_detail(self, product: Dict[str, Any], product_id: str) -> Dict[str, Any]:
        """Transform scraped product detail to standard format."""
        if isinstance(product, list):
            product = product[0]

        basic_info = self._validate_nested_structure(product.get("product_basic_info", {}))
        product_images = self._validate_nested_structure(basic_info.get("images", {}))

        transformed = {
            "name": basic_info.get("name", ""),
            "brand": "",  # Not available in Jiji schema
            "category": "",  # Not available in Jiji schema
            # "product_id": product_id,
            # "url": f"{self.base_url}{product.get('url', '')}",
            "description": product.get("description", ""),
            "current_price": self._clean_price(basic_info.get("current_price", "")),
            "original_price": 0.0,  # Not available in Jiji schema
            "discount": 0.0,  # Not available in Jiji schema
            "image": product_images[0].get("url", "") if product_images else "",
            "images": [
                {
                    "url": img.get("url", ""),
                    "zoom_url": "",  # Not available in Jiji schema
                    "alt": img.get("alt", "")
                }
                for img in product_images
            ],
            "source": self.name,
            "rating": 0,  # Not available in Jiji schema
            "rating_count": 0,  # Not available in Jiji schema
            "seller": {
                "name": "",  # Currently commented out in schema
                "rating": 0  # Not available in Jiji schema
            },
            "specifications": [
                {"label": spec["key"], "value": spec["value"]}
                for spec in product.get("specifications", [])
                if isinstance(spec, dict) and "key" in spec and "value" in spec  # Validate each spec
            ],
            "features": [],  # Not available in Jiji schema
            "reviews": []  # Not available in Jiji schema
        }
        if self.db_manager:
            product = await self.db_manager.get(product_id, tag="list")
            if product:
                transformed.update({
                    "name": product["name"],
                    "product_id": product["product_id"],
                    "current_price": product["current_price"],
                    "original_price": product["original_price"],
                    "discount": product["discount"],
                    "image": product.get("image", product["image"]),
                    "url": product["url"]
                })


        return transformed

    async def get_product_list(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """Get product list by scraping."""
        return await self.extract_product_list(url, **kwargs)

    async def get_product_detail(self, url: str, product_id: str, **kwargs) -> Dict[str, Any]:
        """Get product detail using GraphQL."""
        product = await super().get_product_detail(url, **kwargs)
        return await self._transform_product_detail(product, product_id) 


    async def extract_product_list(self, url, **kwargs):
        from utils._craw4ai import CrawlerManager, AsyncWebCrawler, CrawlerRunConfig
        try:
            # response = await self.client.get(url)
            # html_content = response.text
            config = CrawlerRunConfig(magic=True)

            crawler: AsyncWebCrawler = CrawlerManager().get_crawler()
            response = await crawler.arun(url, config=config)
            print(response)
            html_content = response.html
            print(html_content)

        except Exception as e:
            print(f"URL failed {url} throug {str(e)}")
            products = await super().get_product_list(url, **kwargs)
            return await self._transform_product_list(products)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the script tag containing the product data
        with open("product_page.html", "w", encoding='utf-8') as f:
            f.write(soup.prettify())
            
        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        if script_tag:
            # Extract the JSON data from the script tag
            json_data = script_tag.string
        
            # Parse the JSON data
            data = json.loads(json_data)


            products = data.get('data', {}).get('state', {}).get('adverts_list', [])
            print(products)
            # Iterate over the products and extract relevant information
            ps = []
            for product in products:
                product_id = self.generate_id()

                dt = {
                    "name": product.get('title'),
                    "url": f"{self.base_url}{product.get('url')}",
                    "category": product.get('category_name'),
                    "current_price": product.get('price_obj', {}),
                    "description": product.get('short_description'),
                    "image": product.get('image_obj').get("url"),
                    "images": product.get('images', []),
                    "original_price": 0.0,  
                    "discount": 0.0,
                    "source": self.name,
                    "product_id": product_id
                }
                ps.append(dt)

                await self.db_manager.set(
                    product_id,
                    dt,
                    tag="list"
                )
            print(len(ps))
            return ps

        else:
            print(f"Script tag not found for URL: {url}")
            products = await super().get_product_list(url, **kwargs)
            return await self._transform_product_list(products)
