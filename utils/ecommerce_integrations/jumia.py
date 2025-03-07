from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs
from ..ecommerce.base import ScrapingIntegration
from db.cache.dict import DiskCacheDB

# from ..request_session import http_client

from ..logging import logger
# from utils import db_manager

import json
from bs4 import BeautifulSoup
import httpx


class JumiaIntegration(ScrapingIntegration):
    def __init__(self, db_manager: DiskCacheDB = None):
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
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Upgrade-Insecure-Requests": "1",
            "Cookie": "sponsoredUserId=385174644203393638867825e26aefe8; regeneratedSponsoredUserId=1; newsletter=1; userLanguage=en_NG; _gcl_au=1.1.1401530358.1736597033; _ga=GA1.1.1713371664.1736597033; _fbp=fb.2.1736597034909.22767246798886060; policy=v1.0; __cf_bm=vLxIo9mogJU_D1IY6erMQ2ldoi57DljL8uqxmj9P6aw-1740890595-1.0.1.1-KdTYbhsXkn3gjwlV_e4ZAJu81Iwfej919PmatPo6LqllMbYHxllH5nZWErVa1TwPBYsa1B0DiZ5P2jnhEauvWWaW_IXNRBplNwMNh75ey_s; spadsUid=dadbadd8-f720-11ef-8603-6650dad24c66; sb-closed=true; ABTests=%5B%7B%22name%22%3A%22SearchABTest%22%2C%22scenario%22%3A%22default%22%2C%22updatedAt%22%3A1738156728%7D%2C%7B%22name%22%3A%22Home%22%2C%22scenario%22%3A%22B%22%2C%22updatedAt%22%3A1739269696%7D%2C%7B%22name%22%3A%22MLP%22%2C%22scenario%22%3A%22B%22%2C%22updatedAt%22%3A1622023689%7D%2C%7B%22name%22%3A%22CLP%22%2C%22scenario%22%3A%22A%22%2C%22updatedAt%22%3A1636709906%7D%2C%7B%22name%22%3A%22Cart%22%2C%22scenario%22%3A%22E%22%2C%22updatedAt%22%3A1621344636%7D%2C%7B%22name%22%3A%22SponProdPdp%22%2C%22scenario%22%3A%22A%22%2C%22updatedAt%22%3A1709647935%7D%2C%7B%22name%22%3A%22UserReco%22%2C%22scenario%22%3A%22B%22%2C%22updatedAt%22%3A1725300505%7D%2C%7B%22name%22%3A%22SponProdPdpV3%22%2C%22scenario%22%3A%22B%22%2C%22updatedAt%22%3A1722160470%7D%5D; SOLSESSID=d8773945b31e11b27dfc528282975b47; moe_uuid=c6c67cb5-4dac-4d68-935b-a4457f1467df; cto_bundle=iqRCSV9la2MlMkJBazNucmFZNFRPalNQVWclMkZ1MDl0ZG83MGFjdzB1NFMlMkIxRVV0Y01XUUklMkZPbnlRMUVVZHRqZGJUT2hqeGslMkZNOXhBJTJGeVMlMkJKU1FoSXoxNENoSFIyNzclMkZ3Ujh2bHpGcHE3c3BCQkxFQk5TNnV1RUhYNjM1JTJGbDdtR3piOTZBMjZJMjlVdWk2USUyQkZHQUp5NmhPaSUyRndPVnIxeHpLSmh4cyUyRmZXVFVwZFhyQXhrYXdnbEV1Skd4YjZuU2ZMaDc2cWc4cXRvSWNBbWdVSmh6NTVqdGlSU0hnJTNEJTNE; __gads=ID=8b485637d2c2f7d3:T=1736675404:RT=1740890604:S=ALNI_Mbbk5pwClWSkbdxEf1gqatR5R56vg; __gpi=UID=00000fc69b1cf079:T=1736675404:RT=1740890604:S=ALNI_Ma03UF9WW5oqYHTpI-48VTwa_fQcQ; __eoi=ID=be2289f9fecd04e6:T=1736675404:RT=1740890604:S=AA-AfjYbypTobcw0Nb5Eg90RPt3a; _ga_SDKHD9CQ3C=GS1.1.1740890599.5.0.1740890606.53.0.0; FCNEC=%5B%5B%22AKsRol-CiQG4epcVHQyejndM_vEVtr3zq0wMa9ycCq2Q6eFRkoX930IC1DtxKzCm8yyiUiAxqubICAjQZ_Z5mit2CyLGNs64YabJuq-iQVawvphN2wtxec9KWsKR0DLb130wptem5j0ww4P8n0mdD0G1Oh5tP7KdLg%3D%3D%22%5D%5D"
        }
        self.db_manager = db_manager
        self.session = httpx.AsyncClient(
            headers=self.headers,
            follow_redirects=True,
            timeout=30.0
        )
        
    async def search_via_query(self, product_name: str, country='ng'):
        try:
            search_url = f"https://www.jumia.{country}/catalog/?q={product_name.replace(' ', '+')}"
            result = await self.session.get(search_url)
            return result.text
        except Exception as e:
            logger.error(str(e))
            return None
        
    async def search_via_sku(self, sku: str, country='ng'):
        try:
            search_url =  f"https://www.jumia.{country}/catalog/productspecifications/sku/{sku}"
            result = await self.session.get(search_url)
            return result.text
        except Exception as e:
            logger.error(str(e))
            return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()

    async def _check_url_accessibility(self, url: str) -> bool:
        """Check if URL is accessible using HEAD request first."""
        try:
            await self.session.head(url, follow_redirects=True)
            return True
        except Exception as e:
            print(f"HEAD request failed for {url}: {str(e)}")
            return False

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

    async def _transform_product_list(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform scraped product list to standard format."""
        transformed = []
        for product in products:
            # Handle both relative and absolute URLs
            url = product.get('url', '')
            # print(url)
            # if product_url.startswith('http'):
            #     url = product_url
            # else:
            #     # Remove leading slash if present to avoid double slashes
            #     product_url = product_url.lstrip('/')
            #     url = f"{self.base_url}/{product_url}"

            product_id = self.generate_url_id(url)
            item = {
                "product_id": product_id,
                "name": product.get("name", ""),
                "category": self.extract_category(product.get("name", "")),
                "brand": self.extract_brands(product.get("name", "")),
                "current_price": self._clean_price(product.get("current_price", "")),
                "original_price": self._clean_price(product.get("original_price", "")),
                "discount": self._clean_discount(product.get("discount", "")),
                "image": product.get("image", ""),
                "url": f"{self.base_url}{product.get('url', '')}",
                "source": "jumia",
                "rating": self._clean_rating(product.get("rating", "0")),
                "rating_count": self._clean_rating_count(product.get("rating_count", ""))
            }
            transformed.append(item)

            await self.db_manager.set(
                key=product_id,
                value=item,
                tag="list",
            )
        return transformed


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

    async def _transform_product_detail(self, product: List[Dict[str, Any]] | Dict[str, Any], product_id, url) -> Dict[str, Any]:
        """Transform scraped product detail to standard format."""
        print(url)
        # Validate and normalize structure first
        product = self._validate_product_structure(product)
        if not product:
            return {}

        product["source"] = self.name

        # Validate nested structures
        basic_info = self._validate_nested_structure(product.get("product_basic_info"))
        product_details = self._validate_nested_structure(product.get("product_details"))
        product_reviews = self._validate_nested_structure(product.get("product_reviews"))

        product_detail = {
            "name": basic_info.get("name", ""),
            "brand": basic_info.get("brand", ""),
            "product_id": product_id,
            "url": url,
            "category": product.get("category", "") if product.get("category") else self.extract_category(basic_info.get("name", "")),
            "brand": product.get("brand", "") if product.get("brand") else self.extract_brands(basic_info.get("name", "")),
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
            "source": "jumia",
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
        # if self.db_manager:
        #     product = await self.db_manager.get(product_id, tag="list")
        #     if product:
        #         product_detail.update({
        #             "url": product["url"]
        #         })

        #         print(product['url'])

        return product_detail

    async def get_product_list(self, url: str, query, **kwargs) -> List[Dict[str, Any]]:
        """Get product list by scraping."""
        products = await self.extract_list_data(url,query=query, **kwargs)
        return products
        # return await self._transform_product_list(products)


    async def get_product_detail(self, url: str, product_id: str, **kwargs) -> Dict[str, Any]:
        """Get product detail by scraping."""
        # try:
        #     product = await self.extract_product_detail(url, product_id, **kwargs)
        # except Exception as e:
        #     logger.warning(f"Direct extraction failed for {url}, falling back to base scraper: {str(e)}")
        try:
            product = await super().get_product_detail(url, product_id, custom_headers=self.headers, **kwargs)
            product = await self._transform_product_detail(product, product_id, url)
        except Exception as e:
            logger.error(f"Base scraper also failed for {url}: {str(e)}")
            product = None

        # If both extraction methods fail, try to get basic info from list cache
        if not product and self.db_manager:
            try:
                product = await self.db_manager.get(product_id, tag='list')
                if product:
                    logger.info(f"Retrieved basic product info from list cache for {product_id}")
            except Exception as e:
                logger.error(f"Error accessing list cache for product {product_id}: {str(e)}")

    
        return product if product else {}
    

    async def extract_product_detail(self, url: str, product_id: str, **kwargs) -> Dict[str, Any]:
        """Extract product detail using the window.__STORE__ data."""
        html_content = None

        # Try to get cached product first
        if self.db_manager:
            product = await self.db_manager.get(product_id, 'list')
            if product and product.get('sku'):
                # First attempt: Try getting details via SKU
                html_content = await self.search_via_sku(product['sku'])
                if html_content is not None:
                    logger.info(f"Successfully fetched product details via SKU for {product_id}")

        # Second attempt: Try direct URL if SKU lookup failed or wasn't possible
        if not html_content:
            try:
                # Check URL accessibility first
                if await self._check_url_accessibility(url):
                    response = await self.session.get(url)
                    html_content = response.text
                    logger.info(f"Successfully fetched product details via URL for {product_id}")
                else:
                    logger.warning(f"URL not accessible for product {product_id}: {url}")
            except Exception as e:
                logger.error(f"Failed to fetch product detail via URL for {product_id}: {str(e)}")
                raise Exception(f"Failed to fetch product detail: {str(e)}")

        if not html_content:
            raise Exception("Could not fetch product details via SKU or URL")

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the script tag containing the product data
        script_tag = soup.find('script', text=lambda t: t and 'window.__STORE__' in t)
        
        if not script_tag:
            raise Exception("Product data not found in page")

        # Extract the JSON data from the script tag
        script_content = script_tag.string
        json_data = script_content.split('window.__STORE__=', 1)[-1].strip(';')
        
        try:
            # Parse the JSON data
            data = json.loads(json_data)
            
            # Extract product information
            product = data.get('product', {})
            if not product:
                raise Exception("No product data found in store")

            # Extract specifications
            specs = []
            for spec_group in product.get('specifications', []):
                for spec in spec_group.get('values', []):
                    specs.append({
                        "label": spec_group.get('name', ''),
                        "value": spec
                    })

            # Extract reviews
            reviews = []
            for review in product.get('reviews', {}).get('items', []):
                reviews.append({
                    "rating": self._clean_rating(review.get('rating', 0)),
                    "title": review.get('title', ''),
                    "comment": review.get('comment', ''),
                    "date": review.get('created_at', ''),
                    "author": review.get('reviewer_name', ''),
                    "verified": review.get('is_verified_purchase', False)
                })

            # Build the product detail object
            product_detail = {
                "product_id": product_id,
                "name": product.get('name', ''),
                "brand": product.get('brand', {}).get('name', ''),
                "category": product.get('category', {}).get('name', ''),
                "description": product.get('description', ''),
                "current_price": float(product.get('price', {}).get('amount', 0)),
                "original_price": self._clean_price(product.get('price', {}).get('old_amount', '')),
                "discount": self._clean_discount(product.get('price', {}).get('discount', '')),
                "url": url,
                "image": product.get('image', {}).get('url', ''),
                "images": [img.get('url', '') for img in product.get('images', [])],
                "source": self.name,
                "rating": self._clean_rating(product.get('rating', {}).get('average', 0)),
                "rating_count": self._clean_rating_count(product.get('rating', {}).get('count', 0)),
                "specifications": specs,
                "reviews": reviews,
                "seller": {
                    "name": product.get('seller', {}).get('name', ''),
                    "rating": self._clean_rating(product.get('seller', {}).get('rating', {}).get('average', 0))
                }
            }

            return product_detail

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse product JSON for {product_id}: {str(e)}")
            raise Exception("Failed to parse product data")
        except Exception as e:
            logger.error(f"Error processing product detail for {product_id}: {str(e)}")
            raise

    async def extract_list_data(self, url: str, query, **kwargs) -> List[Dict[str, Any]]:
        html_content = await self.search_via_query(query)

        if html_content is None:
            try:
                # First check URL accessibility with HEAD request
                if not await self._check_url_accessibility(url):
                    raise Exception("URL not accessible")
                    
                # If HEAD request successful, proceed with GET
                response = await self.session.get(url)
                html_content = response.text
            except Exception as e:
                print(f"URL failed {url} through {str(e)}")
                products = await super().get_product_list(url, custom_headers=self.headers, **kwargs)
                return await self._transform_product_list(products)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the script tag containing the product data
        script_tag = soup.find('script', text=lambda t: t and 'window.__STORE__' in t)
        
        if script_tag:
            # Extract the JSON data from the script tag
            script_content = script_tag.string
            json_data = script_content.split('window.__STORE__=', 1)[-1].strip(';')
            
            # Parse the JSON data
            data = json.loads(json_data)
            
            # Extract product information
            products = data.get('products', [])

            # List to store extracted product data
            product_list = []
            
            for product in products:
                url = f"{self.base_url}{product.get('url', '')}"
                product_id = self.generate_url_id(url)
                product_info = {
                    "sku": product.get("sku", None),
                    "product_id": product_id,
                    'category': product.get('categories', '')[0],
                    'name': product.get('displayName', ''),
                    'brand': product.get('brand', ''),
                    'current_price': float(product.get('prices', {}).get('rawPrice', '')),
                    'old_price': self._clean_price(product.get('prices', {}).get('oldPrice', '')),
                    'discount':self._clean_discount(product.get('prices', {}).get('discount', '')),
                    'rating': product.get('rating', {}).get('average', ''),
                    'rating_count': product.get('rating', {}).get('totalRatings', ''),
                    'image': product.get('image', ''),
                    'url': url,
                    'source': self.name
                }
                product_list.append(product_info)

                await self.db_manager.set(
                    key=product_id,
                    value=product_info,
                    tag="list",
                    )
            
            return product_list
        else:
            print(f"URL failed {url}")
            products = await super().get_product_list(url, **kwargs)
            return await self._transform_product_list(products)