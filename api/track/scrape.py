from urllib.parse import urlparse
from typing import TypeVar, Any, Dict, Union, List
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


    async def get_jumia_product(self, url: str, product_id: str)-> Dict[str, Any]:
        from utils._craw4ai import  AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig

        extraction_strategy= JsonCssExtractionStrategy(schema=self.get_jumia_schema(), verbose=True)

        scraper: AsyncWebCrawler  = await self.get_crawler()
        response = await scraper.arun(url=url, extraction_strategy=extraction_strategy, bypass_cache=True)
        extracted_content = loads(response.extracted_content)
        if not extracted_content:
            return {}

        extracted_content = extracted_content[0] if isinstance(extracted_content, list) else extracted_content if extracted_content else {}

        product = self._validate_product_structure(extracted_content)
        if not product:
            return {}

        product["source"] = "jumia"

        # Validate nested structures
        basic_info = self._validate_nested_structure(product.get("product_basic_info"))
        product_details = self._validate_nested_structure(product.get("product_details"))
        product_reviews = self._validate_nested_structure(product.get("product_reviews"))

        return {
                "name": basic_info.get("name", ""),
                "brand": basic_info.get("brand", ""),
                "product_id": product_id,
                "url": f"jumia.com.ng{product.get('url', '')}",
                "category": product.get("category", ""),
                "brand": product.get("brand", ""),
                "description": "",  # Not directly available in schema
                "current_price": self._clean_price(basic_info.get("current_price", "")),
                "original_price": self._clean_price(basic_info.get("original_price", "")),
                "discount": self._clean_discount(basic_info.get("discount", "")),
                "image": basic_info.get("images", [{}])[0].get("url", "") if basic_info.get("images") else "",
                "images": [
                    {
                        "url": img.get("url", ""),
                        "zoom_url": img.get("zoom_url", ""),
                        "alt": img.get("alt", "")
                    }
                    for img in basic_info.get("images", [])
                ],
                "source": "Jumia",
                "rating": self._clean_rating(basic_info.get("rating", "0")),
                "rating_count": self._clean_rating_count(basic_info.get("reviews_count", "")),
                "seller": {
                    "name": "",  # Not available in schema
                    "rating": 0  # Not available in schema
                },
                "specifications": self._clean_specifications(product_details.get("specifications", [])),
                "features": self._clean_features(product_details.get("features", [])),
                "reviews": [
                    {
                        "rating": self._clean_rating(review.get("rating", "0")),
                        "title": review.get("title", ""),
                        "comment": review.get("comment", ""),
                        "date": review.get("date", ""),
                        "author": review.get("author", ""),
                        "verified": review.get("verified", False)
                    }
                    for review in product_reviews.get("reviews", [])
                ]
            }
            

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
                "source": "Konga",
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
                "url": f"konga.com/product/{hit.get('url_key', '')}",
                
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
  
    async def get_jiji_product(self, url: str, product_id: str)-> Dict[str, Any]:
        from utils._craw4ai import  AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig

        # # wait_for_images=True,
        config = CrawlerRunConfig(
            bypass_cache=True,
            wait_for="body",
            extraction_strategy= JsonCssExtractionStrategy(schema=self.get_jiji_schema())
        )

        scraper: AsyncWebCrawler  = await self.get_crawler()
        response = await scraper.arun(url=url, config=config)
        extracted_content = loads(response.extracted_content)
        extracted_content = extracted_content[0] if isinstance(extracted_content, list) else extracted_content if extracted_content else {}
   

        soup = BeautifulSoup(response.html, 'html.parser')
        images = self.get_jji_images(soup)
        title_tag = soup.title.string
        product_name_from_title = title_tag.split(" in ")[0]

        description_meta_tag = soup.find("meta", attrs={"name": "description"})
        description_from_meta = description_meta_tag["content"] if description_meta_tag else None

        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})

        if script_tag:
            # Parse the JSON data from the script tag
            data = loads(script_tag.string)

            price = self.find_price(data)
            if isinstance(price, str):
                try:
                    price =  float(price)
                    
                except ValueError:
                    price = 0.0
        else:
            price = 0.0

        
        return {
            "product_id": product_id,
            "current_price": price,
            "name": product_name_from_title,
            "original_price": None,
            "description": description_from_meta,
            "original_price": 0.0,
            "images": images,
            "source": "Jiji",
            "rating": 0,  
            "rating_count": 0, 
            "seller": {
                "name": "",  
                "rating": 0 
            },
            "specifications": [
                {"label": spec["key"], "value": spec["value"]}
                for spec in extracted_content.get("specifications", [])
                if isinstance(spec, dict) and "key" in spec and "value" in spec  # Validate each spec
            ],
        }
    def is_valid_image_url(self, url: str):
        return url.lower().endswith((".jpg", ".webp"))

    def get_jji_images(self, soup: BeautifulSoup):
        og_image_tag = soup.find("meta", property="og:image")
        image_src_tag = soup.find("link", rel="image_src")

        # Extract images from <img> tags in the body
        image_tags = soup.find_all("img")

        # Combine all image URLs into a list of dictionaries
        product_images = []

        # Add og:image and image_src URLs
        if og_image_tag:
            product_images.append({
                "url": og_image_tag["content"],
                "zoom_url": "",  # Not available in Jiji schema
                "alt": "Primary product image"  # Default alt text
            })

        if image_src_tag:
            product_images.append({
                "url": image_src_tag["href"],
                "zoom_url": "",  # Not available in Jiji schema
                "alt": "Primary product image"  # Default alt text
            })

        # Add images from <img> tags
        for img in image_tags:
            if "src" in img.attrs and self.is_valid_image_url(img["src"]):
                product_images.append({
                    "url": img["src"],
                    "zoom_url": "",  # Not available in Jiji schema
                    "alt": img.get("alt", "")  # Use the alt attribute if available
                })

        # Format the result
        return product_images

        

    def find_price(self, data):
        # Check if the data is a dictionary
        if isinstance(data, dict):
            # Iterate through the dictionary
            for key, value in data.items():
                # If the key is 'product:price:amount', return the value
                if key == 'product:price:amount':
                    return value
                # Otherwise, recursively search through the value
                result = self.find_price(value)
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
                result = self.find_price(item)
                if result is not None:
                    return result
        # Return None if the price is not found
        return None

        # return extracted_content

    def extract_source(self, url) -> str:
        # If url is bytes, decode it to a string
        if isinstance(url, bytes):
            url = url.decode('utf-8')
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        # If domain is still bytes, decode it as well
        if isinstance(domain, bytes):
            domain = domain.decode('utf-8')
        
        # Identify the source based on the domain
        if "jumia.com.ng" in domain:
            return "jumia"
        elif "jiji.ng" in domain:
            return "jiji"
        elif "konga.com" in domain:
            return "konga"

                

    async def get_product_details(
        self,
        product_id: str,
    ) -> Dict[str, Any]:
        
        # url = ID.decrypt(product_id)
        url = self.shortener.enlarge_url(product_id)
        source = self.extract_source(url)

        print(url, source)
        
        if source == "jiji":
            return await self.get_jiji_product(url, product_id)
        elif source == "jumia":
            return await self.get_jumia_product(url, product_id)

        elif source == "konga":
            return await self.get_konga_product(url)

        else:
            raise Exception("Product was not found")

    def _clean_specifications(self, specifications: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Clean and format specifications data."""
        cleaned_specs = []
        for spec in specifications:
            label = spec.get("label", "").strip().replace(":", "")
            value = spec.get("value", "").strip()
            
            # Remove label from value if it's repeated
            if value.startswith(f"{label}:"):
                value = value[len(label)+1:].strip()
            
            # Split on colon if value contains both label and value
            if ":" in value and not label:
                label, value = value.split(":", 1)
                label = label.strip()
                value = value.strip()
            
            if label and value:
                cleaned_specs.append({
                    "label": label,
                    "value": value
                })
        return cleaned_specs

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

    def _clean_features(self, features: List[Dict[str, str]]) -> List[str]:
        """Clean and format features data."""
        cleaned_features = []
        for feature in features:
            feature_text = feature.get("feature", "").strip()
            if feature_text:
                # Remove redundant "Feature:" prefix if present
                if feature_text.lower().startswith("feature:"):
                    feature_text = feature_text[8:].strip()
                cleaned_features.append(feature_text)
        return cleaned_features

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
    def _validate_product_structure(self, product: Any) -> Dict[str, Any]:
        """Validate and normalize product structure before processing."""
        if not product:
            return {}
            
        if isinstance(product, list):
            if not product:  # Empty list
                return {}
            return product[0] if isinstance(product[0], dict) else {}
            
        if isinstance(product, dict):
            return product
            
        return {}

    def _clean_rating_count(self, count: str) -> int:
        """Extract rating count from string."""
        if not count:
            return 0
        # Example: "(123 ratings)" -> 123
        try:
            return int(''.join(filter(str.isdigit, count)))
        except ValueError:
            return 0

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

    def get_jumia_schema(self):
        return {
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
                                "selector": "div.-pvxs > a:nth-child(1)",
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
                    },
                    
                ]
            }


    def get_jiji_schema(self):
        return {
                "name": "Jiji Product Detail Schema",
                "baseSelector": ".b-advert-seller-info-wrapper",
                "fields": [
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


scraper = EcommerceWebScraper()