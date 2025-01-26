from typing import TypeVar, Any, Dict, Union
from json import loads, dump

from crawl4ai import AsyncWebCrawler

from utils.logging import logger
from config import USER_AGENT, KONGA_API_KEY, KONGA_ID

from bs4 import BeautifulSoup
from pydantic import BaseModel
from algoliasearch.search.client import SearchClient

from utils.url_shortener import URLShortener


T = TypeVar('T', bound=BaseModel)


class EcommerceWebScraper:
    konga_index_name = "catalog_store_konga_price_asc"

    def __init__(
        self, 
        no_words: int = 500,
        schema: T = None,
        ) -> None:

        self.konga_client = SearchClient(KONGA_ID, KONGA_API_KEY)
        self.header = {"User-Agent": USER_AGENT}
        self.shortener = URLShortener()


    async def get(self, url):
        from utils.request_session import http_client
        return await http_client.get(url)


    async def get_crawler(self)-> AsyncWebCrawler: 
        from utils._craw4ai import CrawlerManager
        return await CrawlerManager.get_crawler()


    async def get_jumia_product(self, url: str)-> Dict[str, Any]:
        response = await self.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the script tag containing the product data
        script_tag = soup.find('script', text=lambda t: t and 'window.__STORE__' in t)
        
        if script_tag:
            # Extract the JSON data from the script tag
            script_content = script_tag.string
            json_data = script_content.split('window.__STORE__=', 1)[-1].strip(';')
            
            # Parse the JSON data
            data = loads(json_data)

            with open("jumia.json", "w") as f:
                dump(data, f, indent=4)


            if 'products' in data and len(data['products']) > 0:
                product: dict = data['products'][0]

                return {
                    'category': product.get('categories', '')[0],
                    'name': product.get('displayName', ''),
                    'brand': product.get('brand', ''),
                    'current_price': float(product.get('prices', {}).get('rawPrice', '')),
                    'old_price': self._clean_price(product.get('prices', {}).get('oldPrice', '')),
                    'discount':self._clean_discount(product.get('prices', {}).get('discount', '')),
                    'rating': product.get('rating', {}).get('average', ''),
                    'rating_count': product.get('rating', {}).get('totalRatings', ''),
                    'image': product.get('image', ''),
                    'url': f"www.jumia.com.ng{product.get('url', '')}",
                    'source': "jumia"
                }
                
        else:
            return {}
            

    async def get_konga_product(self, product_id: str)-> Dict[str, Any]:
        hit =  await self.konga_client.get_object(self.konga_index_name, product_id)
        with open("konga.json", "w") as f:
            dump(hit, f, indent=4)
        return  {
                "product_id": product_id,
                "name": hit.get("name", ""),
                "brand": hit.get("brand", ""),
                # "category": self.extract_category(hit.get("name", "")),
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
                # "product_id": self.hash_id(f"{self.base_url}/product/{hit.get('url_key', '')}"),
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
  
    async def get_jiji_product(self, url: str)-> Dict[str, Any]:
        from utils._craw4ai import  AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig

        # # wait_for_images=True,
        # config = CrawlerRunConfig(
        #     bypass_cache=True,
        #     wait_for="body",
        #     extraction_strategy= JsonCssExtractionStrategy(schema=self.get_jiji_schema())
        # )

        scraper: AsyncWebCrawler  = await self.get_crawler()
        response = await scraper.arun(url=url)
        print(response.html)
        extracted_content = loads(response.extracted_content)
        print(extracted_content)

        # print(extracted_content)
        with open("jiji.html", "w", encoding='utf-8') as f:
            f.write(response.html)

        # return extracted_content



    def find_product(self, data)-> Dict[str, Any]:
        # Check if the data is a dictionary
        product = {}
        if isinstance(data, dict):
            # Iterate through the dictionary
            for key, value in data.items():
                # If the key is 'product:price:amount', return the value
                if key == 'product:price:amount':
                    product["current_price"] = value
                 
                # Otherwise, recursively search through the value
                result = self.find_product(value)
                if result is not None:
                    return result
        # Check if the data is a list
        elif isinstance(data, list):
            p_id = None
            # Iterate through the list
            for id, item in enumerate(data):
                # If the item is a string and matches 'product:price:amount', note its position
                if isinstance(item, str) and item == 'product:price:amount':
                    p_id = id
                    break

            # If 'product:price:amount' was found, return the next item in the list
            if p_id is not None and p_id + 1 < len(data):
                return data[p_id + 1]


            # Otherwise, recursively search through each item in the list
            for item in data:
                result = self.find_product(item)
                if result is not None:
                    return result
        # Return None if the price is not found
        return None
                

    async def get_product_details(
        self,
        url: str,
        source: str,
    ) -> Dict[str, Any]:
        
        # url = ID.decrypt(product_id)
        # url = self.shortener.enlarge_url(product_id)
        
        if source == "jiji":
            return await self.get_jiji_product(url)
        elif source == "jumia":
            return await self.get_jumia_product(url)
        elif source == "konga":
            return await self.get_konga_product(url)



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


    def _clean_price(self, price: str) -> float:
        """Clean price string and convert to float."""
        if not price:
            return 0.0
        # Remove currency symbol, commas, and extra spaces
        cleaned = price.replace("₦", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    def _clean_discount(self, discount: str) -> float:
        """Convert discount string to float percentage."""
        if not discount:
            return 0.0
        # Extract number from strings like "-25%" or "25% OFF"
        try:
            return float(''.join(filter(str.isdigit, discount)))
        except (ValueError, TypeError):
            return 0.0

    def get_jiji_schema(self):
        return {
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
                                "selector": "h1.qa-advert-title",  # Fixed: Removed erroneous .h1 class selector
                                "type": "text"
                            },
                            {
                                "name": "current_price",
                                "selector": "span.qa-advert-price-view-value",
                                "type": "text"
                            },
                            {
                                "name": "images",
                                "selector": "img.qa-carousel-slide", # // Direct image selector
                                "type": "list",
                                "fields": [
                                    {
                                        "name": "url",
                                        "selector": "img", # // Simplified selector
                                        "type": "attribute",
                                        "attribute": "src" # // Use src instead of srcset for direct URL
                                    },
                                    {
                                        "name": "alt",
                                        "selector": "img",
                                        "type": "attribute",
                                        "attribute": "alt",
                                        "optional": True
                                    }
                                ]
                            },
                        ]
                    },
                    {
                        "name": "seller",
                        "type": "nested",
                        "fields": [
                            {
                                "name": "name",
                                "selector": "div.b-advert-user-info__name",
                                "type": "text"
                            },
                            {
                                "name": "verified",
                                "selector": "div.b-advert-user-info i.verified-business-icon",
                                "type": "exists",
                                "optional": True
                            },
                            {
                                "name": "member_since",
                                "selector": "div.b-advert-user-info__date",
                                "type": "text",
                                "optional": True
                            },
                            {
                                "name": "phone",
                                "selector": "div.b-advert-user-info__phone",
                                "type": "text",
                                "optional": True
                            }
                        ]
                    },
                    
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


