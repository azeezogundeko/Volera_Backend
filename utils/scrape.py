import asyncio
from typing import List, Dict, TypeVar

from utils.logging import logger
from config import USER_AGENT

from .request_session import http_client

from langchain_community.document_loaders import AsyncHtmlLoader, AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer, Html2TextTransformer
from langchain.schema import Document

from pydantic import BaseModel


T = TypeVar('T', bound=BaseModel)

class Doc:
    def __init__(self, url, page_content):
        self.url = url
        self.page_content = page_content

    def __str__(self):
        return f"Doc(url={self.url}, page_content={self.page_content})"

    def to_dict(self):
        return {"url": self.url, "page_content": self.page_content}

class TrackerWebScraper:
    def __init__(
        self, 
        no_words: int = 500,
        schema: T = None,
        ) -> None:
        """
        Initialize the scraper with optional URLs.
        """
        self.no_words = no_words
        self.soup_transformer = BeautifulSoupTransformer()
        self.html2text_transformer = Html2TextTransformer()
        self.schema = schema
        self.header = {"User-Agent": USER_AGENT}
        self.client = http_client

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
        
    async def scrape(
        self,
        urls: List[str],
        timeout: int = 5,
        retries=3,
        rate_limit=5,
        ignore_errors=True,
        site_name: str = None,
        use_js: bool = False,
        tags: List[str] = None,
        plain_text: bool = False
    ) ->List[Document]:
        """
        Scrape websites and extract content based on tags or plain text.

        :param urls: List of URLs to scrape.
        :param use_js: Use JavaScript-enabled scraping if True.
        :param tags: List of tags to extract content from (if plain_text is False).
        :param plain_text: Extract plain text instead of tag-based content if True.
        :return: Extracted content as a dictionary.
        """

        from .request_session import http_client
        from . import _craw4ai as craw4ai

        



    async def scrape_websites(
        self,
        urls: List[str],
        timeout: int = 10,  
        retries: int = 3,   
        rate_limit: int = 5, 
        ignore_errors: bool = True
    ) -> List[Document]:
        """
        Scrape websites asynchronously with error and timeout handling.

        Args:
            urls (List[str]): List of URLs to scrape.
            timeout (int): Timeout for each request in seconds.
            retries (int): Number of retries for failed requests.
            rate_limit (int): Max number of concurrent requests.
            ignore_errors (bool): Whether to ignore errors and continue.

        Returns:
            List[Document]: Successfully scraped documents.
        """
        async def fetch(url: str, session: ClientSession, attempt: int = 1) -> Document:
            try:
                async with session.get(url, timeout=ClientTimeout(total=timeout)) as response:
                    text = await response.text()
                    return Doc(url, text)

                    # loader = AsyncHtmlLoader(web_path=url)  
                    # return loader._to_document(url, text)
            except Exception as e:
                if attempt < retries:
                    return await fetch(url, session, attempt + 1)
                if not ignore_errors:
                    raise e
                logger.info(f"Failed to fetch {url} after {retries} attempts: {e}")
                return None

        semaphore = asyncio.Semaphore(rate_limit)

        async def fetch_with_limit(url: str, session: ClientSession):
            async with semaphore:
                return await fetch(url, session)

        async with ClientSession() as session:
            tasks = [fetch_with_limit(url, session) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and return only successful documents
        return [result for result in results if isinstance(result, Doc) and result.page_content]

