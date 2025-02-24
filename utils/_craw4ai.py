from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import (
    LLMExtractionStrategy,
    JsonCssExtractionStrategy,
    CosineStrategy
)
import requests
import socks
import socket
import asyncio

class TorProxyConfig(BaseModel):
    """Configuration for Tor proxy settings"""
    host: str = "127.0.0.1"
    port: int = 9050
    enabled: bool = False

class CrawlerManager:
    _instance = None
    _crawler = None
    _tor_config: TorProxyConfig = TorProxyConfig()
    
    @classmethod
    async def initialize(cls, use_tor: bool = False, tor_host: str = "127.0.0.1", tor_port: int = 9050):
        """Initialize the crawler instance if it doesn't exist"""
        if cls._crawler is None:
            # Configure Tor proxy if enabled
            if use_tor:
                cls._tor_config = TorProxyConfig(
                    host=tor_host,
                    port=tor_port,
                    enabled=True
                )
                # Configure global socket to use SOCKS5 proxy
                socks.set_default_proxy(socks.SOCKS5, tor_host, tor_port)
                socket.socket = socks.socksocket
                print("Tor proxy enabled")
            
            # Initialize crawler with proxy settings if Tor is enabled
            proxy_settings = None
            if cls._tor_config.enabled:
                proxy_settings = f"socks5h://{cls._tor_config.host}:{cls._tor_config.port}"
                print("Tor proxy settings: ", proxy_settings)
            
            # Create crawler with default config
            # config = CrawlerRunConfig(
            #     magic=True,
            #     parser_type='html.parser',
            #     only_text=False,
            #     excluded_tags=[],
            #     keep_data_attributes=True
            # )
            
            cls._crawler = AsyncWebCrawler(
                verbose=True,
                # config=config,
                proxy=proxy_settings  # Set proxy at crawler level
            )
            await cls._crawler.__aenter__()
    
    @classmethod
    async def get_crawler(cls) -> AsyncWebCrawler:
        """Get the singleton crawler instance"""
        if cls._crawler is None:
            await cls.initialize()
        return cls._crawler
    
    @classmethod
    async def cleanup(cls):
        """Cleanup the crawler instance"""
        if cls._crawler is not None:
            await cls._crawler.__aexit__(None, None, None)
            cls._crawler = None
    
    @classmethod
    async def rotate_tor_ip(cls):
        """Request a new Tor circuit to get a new IP address"""
        if not cls._tor_config.enabled:
            return False
            
        try:
            # Create a new circuit
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((cls._tor_config.host, cls._tor_config.port))
                s.send(b'AUTHENTICATE ""\r\n')
                s.send(b'SIGNAL NEWNYM\r\n')
                
            # Wait a bit for the new circuit
            await asyncio.sleep(5)
            
            # Verify IP change
            proxy = f"socks5h://{cls._tor_config.host}:{cls._tor_config.port}"
            response = requests.get(
                "https://check.torproject.org/api/ip",
                proxies={"http": proxy, "https": proxy}
            )
            return response.ok
            
        except Exception as e:
            print(f"Failed to rotate Tor IP: {str(e)}")
            return False
    
    @classmethod
    async def get_current_ip(cls) -> Optional[str]:
        """Get the current IP address being used"""
        if not cls._tor_config.enabled:
            try:
                response = requests.get("https://api.ipify.org?format=json")
                return response.json().get("ip")
            except:
                return None
                
        try:
            proxy = f"socks5h://{cls._tor_config.host}:{cls._tor_config.port}"
            response = requests.get(
                "https://check.torproject.org/api/ip",
                proxies={"http": proxy, "https": proxy}
            )
            return response.json().get("IP")
        except:
            return None

class WebChatResponse(BaseModel):
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    similar_chunks: Optional[List[Dict[str, Any]]] = None

async def chat_with_webpage(
    url: str,
    query: str,
    llm_provider: str = "ollama/nemotron",
    api_token: Optional[str] = None
) -> WebChatResponse:
    """
    Chat with a webpage using LLM-based extraction.
    
    Args:
        url: The webpage URL to chat with
        query: User's query about the webpage
        llm_provider: LLM provider to use (e.g., "ollama/nemotron")
        api_token: API token if required by the LLM provider
    """
    crawler = await CrawlerManager.get_crawler()
    
    # Extract main content
    result = await crawler.arun(
        url=url,
        word_count_threshold=10,
        exclude_external_links=True
    )
    
    # Use LLM to process the query
    strategy = LLMExtractionStrategy(
        provider=llm_provider,
        api_token=api_token,
        instruction=f"Answer the following question about the content: {query}"
    )
    
    llm_result = await crawler.arun(
        url=url,
        extraction_strategy=strategy
    )
    
    return WebChatResponse(
        content=json.loads(llm_result.extracted_content),
        structured_data={"markdown": result.fit_markdown}
    )

async def get_html(url: str, config: CrawlerRunConfig = None, **kwargs):
    reponse = await CrawlerManager.get_crawler().arun(
        url=url,
        config=config,
        exclude_external_links=False,
    )
    return reponse.html

async def get_similar_chunks(
    url: str,
    query: str,
    top_k: int = 3,
    sim_threshold: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Get similar content chunks from a webpage based on a query.
    
    Args:
        url: The webpage URL to analyze
        query: The query to find similar content for
        top_k: Number of top similar chunks to return
        sim_threshold: Similarity threshold (0.0 to 1.0)
    """
    crawler = await CrawlerManager.get_crawler()
    
    strategy = CosineStrategy(
        semantic_filter=query,
        word_count_threshold=10,
        sim_threshold=sim_threshold,
        top_k=top_k
    )
    
    result = await crawler.arun(
        url=url,
        extraction_strategy=strategy
    )
    
    return json.loads(result.extracted_content)

async def extract_structured_data(
    url: str,
    schema: Dict[str, Any],
    use_pattern: bool = False,
    provider: str = "ollama/nemotron",
    api_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract structured data from a webpage using either LLM or pattern-based extraction.
    
    Args:
        url: The webpage URL to extract data from
        schema: The schema defining the structure to extract
        use_pattern: Whether to use pattern-based extraction (True) or LLM-based extraction (False)
    """
    crawler = await CrawlerManager.get_crawler()
    
    if use_pattern:
        strategy = JsonCssExtractionStrategy(schema)
    else:
        strategy = LLMExtractionStrategy(
            provider=provider,
            api_token=api_token,
            schema=schema,
            instruction="Extract structured data according to the schema"
        )
    
    result = await crawler.arun(
        url=url,
        extraction_strategy=strategy
    )
    
    return json.loads(result.extracted_content)

async def filter_webpage_content(
    url: str,
    filters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Filter webpage content based on specified criteria.
    
    Args:
        url: The webpage URL to filter
        filters: Dictionary of filter parameters:
            - word_count_threshold: Minimum words per block
            - exclude_external_links: Whether to exclude external links
            - exclude_external_images: Whether to exclude external images
            - excluded_tags: List of HTML tags to exclude
    """
    crawler = await CrawlerManager.get_crawler()
    
    result = await crawler.arun(
        url=url,
        word_count_threshold=filters.get('word_count_threshold', 10),
        exclude_external_links=filters.get('exclude_external_links', True),
        exclude_external_images=filters.get('exclude_external_images', True),
        excluded_tags=filters.get('excluded_tags', ['form', 'nav'])
    )
    
    return {
        "content": result.fit_markdown,
        "media": result.media,
        "html": result.cleaned_html
    }

async def extract_data_with_css(
    url: str,
    schema: dict,
    bypass_cache: bool = True
) -> List[Dict[str, Any]]:
    """
    Extract structured data from a webpage using CSS selectors.
    
    Args:
        url: The webpage URL to extract data from
        base_selector: CSS selector for the repeating elements
        fields: List of fields to extract, each with 'name', 'selector', and 'type'
        js_code: Optional JavaScript code to execute before extraction
        wait_for: Optional CSS selector to wait for before extraction
        bypass_cache: Whether to bypass the crawler's cache
        
    Returns:
        List of extracted data items matching the schema
    """
    crawler = await CrawlerManager.get_crawler()
    
    strategy = JsonCssExtractionStrategy(schema, verbose=True)
    
    result = await crawler.arun(
        url=url,
        extraction_strategy=strategy,
        bypass_cache=bypass_cache
    )
    if not result.success:
        return []
        
    return json.loads(result.extracted_content)
