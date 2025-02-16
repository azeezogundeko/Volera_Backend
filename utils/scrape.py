from json import loads
from crawl4ai import AsyncWebCrawler

from utils.logging import logger
from config import USER_AGENT, KONGA_API_KEY, KONGA_ID

from bs4 import BeautifulSoup
# from pydantic import BaseModel
from algoliasearch.search.client import SearchClient


# T = TypeVar('T', bound=BaseModel)


class TrackerWebScraper:
    konga_index_name = "catalog_store_konga_price_asc"
    def __init__(
        self, 
        no_words: int = 500
        ) -> None:
        from utils._craw4a import CrawlerManager
        from utils.request_session import http_client

        self.konga_client = SearchClient(KONGA_ID, KONGA_API_KEY)

        self.no_words = no_words
        self.crawler_manager: CrawlerManager = None
        self.client = http_client
        self.header = {"User-Agent": USER_AGENT}

    def __jiji_schema(self):
        return {
        "name": "NuxtData",
        "baseSelector": "script#__NUXT_DATA__",
        "fields": [
            {
                "name": "nuxt_data",
                "selector": "script#__NUXT_DATA__",
                "type": "text" 
            }
        ]
    }

    # async def get(self, url):
    #     async with self.client as client:
    #         return await client.get(url)

    async def get_crawler(self)-> AsyncWebCrawler: 
        if self.crawler_manager is None:
            from utils._craw4a import CrawlerManager
            self.crawler_manager = await CrawlerManager.get_crawler()

        return self.crawler_manager


    async def get_jumia_price(self, url: str)-> float:
        response = await self.client.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the script tag containing the product data
        script_tag = soup.find('script', text=lambda t: t and 'window.__STORE__' in t)
        
        if script_tag:
            # Extract the JSON data from the script tag
            script_content = script_tag.string
            json_data = script_content.split('window.__STORE__=', 1)[-1].strip(';')
            
            # Parse the JSON data
            data = loads(json_data)

            # with open("jiji.json", )

            if 'products' in data and len(data['products']) > 0:
                product = data['products'][0]
                price = product.get('prices', {}).get('rawPrice', 0.0)
                return float(price)

        else:
            return 0.0
            

    async def get_konga_price(self, product_id: str)-> float:
        response =  await self.konga_client.get_object(self.konga_index_name, product_id)
        return response["price"]
  
    async def get_jiji_price(self, url: str)-> float:
        scraper: AsyncWebCrawler  = await self.get_crawler()
        response = await scraper.arun(url=url, bypass_cache=True)

        soup = BeautifulSoup(response.html, 'html.parser')

        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})

        if script_tag:
            # Parse the JSON data from the script tag
            data = loads(script_tag.string)

            price = self.find_price(data)
            if isinstance(price, str):
                try:
                    return float(price)
                except ValueError:
                    return None
        else:
            return None

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
                

    async def get_price(
        self,
        url: str,
        source: str,
    ) -> float:
        
        if source == "jiji":
            return await self.get_jiji_price(url)
        elif source == "jumia":
            return await self.get_jumia_price(url)
        elif source == "konga":
            return await self.get_konga_price(url)
        