from typing import List, Dict, Any

from .schema import extractor
from ...ecommerce.base import EcommerceIntegration
from db.cache.dict import DiskCacheDB


class LLMIntegration(EcommerceIntegration): 
    def __init__(
        self,
        name: str,
        base_url: str,
        url_patterns: List[str],
        db_manager: DiskCacheDB = None
    ):
        super().__init__(name, base_url, url_patterns, "scraping")
        self.db_manager = db_manager
        self.name = name

    async def get_product_list(self, url: str, bypass_cache, query) -> List[Dict[str, Any]]:
        product_id = self.generate_url_id(url)
        products = await extractor.extract_products([url])
        products = products[url]

        # print(products)

        if "error" in products:
            return []
        
        for product in products:
            product["product_id"] = product_id
            product["source"] = self.name

            await self.db_manager.set(
                    key=product_id,
                    value=product,
                    tag="list",
                )
        
        return products

    async def get_product_detail(self, url: str, product_id: str, bypass_cache) -> Dict[str, Any]:
        # product = await self.db_manager.get(product_id, tag='list')

        products = await extractor.extract_products([url])
        products = products[url]

        if "error" in products:
            return {}
        
        for product in products:
            product["product_id"] = product_id
            product["source"] = self.name

        return products[0]
        # if product is None:
            

        # return product