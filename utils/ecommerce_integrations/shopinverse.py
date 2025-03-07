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

class ShopInverseIntegration(ScrapingIntegration):
    def __init__(self, db_manager: DiskCacheDB = None):
        super().__init__(
            name="shopinverse",
            base_url="https://shopinverse.com",
            url_patterns=["shopinverse.com"],
            list_schema={
                "name": "ShopInverse Product List Schema",
                "baseSelector": "article.prd._fb.col.c-prd",
                "fields": [
                    {
                        "name": "name",
                        "selector": ".name",
                        "type": "text"
                    },
                    {
                        "name": "price",
                        "selector": ".prc",
                        "type": "text"
                    }
                ]
            }
        )
