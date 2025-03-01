from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from crawl4ai.extraction_strategy import (
    LLMExtractionStrategy,
    JsonCssExtractionStrategy,
    CosineStrategy
)
import requests
import socks
import socket
import asyncio
import os
# from fastembed import FastEmbed
import logging
from config import USER_AGENT
from config import PRODUCTION_MODE
from utils.flare_bypasser import flare_bypasser

from utils.logging import logger

CHROME_STORAGE_PATH = os.environ.get('CHROME_STORAGE_PATH', '/app/craw4ai_config/state.json')

class TorProxyConfig(BaseModel):
    """Configuration for Tor proxy settings"""
    host: str = "127.0.0.1"
    port: int = 9050
    enabled: bool = False
    container_name: str = "tor_proxy"

class CrawlerManager:
    _instance = None
    _crawler = None
    _tor_config: TorProxyConfig = TorProxyConfig()
    
    @classmethod
    async def _test_proxy_connection(cls, host: str, port: int) -> bool:
        """Test if proxy connection is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception as e:
            logger.warning(f"Proxy connection test failed: {str(e)}")
            return False

    @classmethod
    async def _get_docker_host(cls) -> str:
        """Get the appropriate host for Docker environment"""
        if os.environ.get('DOCKER_CONTAINER'):
            # If running inside Docker, use the service name
            return cls._tor_config.container_name
        return cls._tor_config.host

    @classmethod
    async def initialize(cls, use_tor: bool = False, tor_host: str = "127.0.0.1", tor_port: int = 9050):
        """Initialize the crawler instance if it doesn't exist"""
        if cls._crawler is None:
            try:
                # Configure Tor proxy if enabled
                if use_tor:
                    # Determine the appropriate host
                    actual_host = await cls._get_docker_host()
                    
                    cls._tor_config = TorProxyConfig(
                        host=actual_host,
                        port=tor_port,
                        enabled=True
                    )
                    
                    # Test proxy connection
                    if not await cls._test_proxy_connection(tor_host, tor_port):
                        logger.warning(f"Tor proxy not accessible at {tor_host}:{tor_port}. Falling back to direct connection.")
                        cls._tor_config.enabled = False
                    else:
                        # Configure global socket to use SOCKS5 proxy
                        socks.set_default_proxy(socks.SOCKS5, actual_host, tor_port)
                        socket.socket = socks.socksocket
                        logger.info(f"Tor proxy enabled at {actual_host}:{tor_port}")
                
                # Initialize crawler with proxy settings if Tor is enabled
                proxy_settings = None
                if cls._tor_config.enabled:
                    proxy_settings = f"socks5h://{cls._tor_config.host}:{cls._tor_config.port}"
                    logger.info(f"Using proxy settings: {proxy_settings}")
                    
                    # Set environment variables for requests
                    os.environ['HTTPS_PROXY'] = proxy_settings
                    os.environ['HTTP_PROXY'] = proxy_settings
                
                # Create crawler instance
                config = BrowserConfig(headless=True, storage_state=CHROME_STORAGE_PATH)
                cls._crawler = AsyncWebCrawler(
                    verbose=True,
                    proxy=proxy_settings,
                    config=config
                )
                await cls._crawler.__aenter__()
                logger.info("Crawler initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize crawler: {str(e)}")
                # Initialize without proxy as fallback
                cls._tor_config.enabled = False
                cls._crawler = AsyncWebCrawler(verbose=True)
                await cls._crawler.__aenter__()
                logger.info("Crawler initialized without proxy (fallback mode)")

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
    bypass_cache: bool = True,
    custom_headers: dict = {},
    custom_user_agent: str = USER_AGENT,
    page_timeout: int = 30000,
    use_flare_bypasser: bool = False,
    **kwargs
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
    crawler.crawler_strategy.set_custom_headers(custom_headers)
    crawler.crawler_strategy.update_user_agent(custom_user_agent)
    
    strategy = JsonCssExtractionStrategy(schema, verbose=True)
    config = CrawlerRunConfig(magic=True, **kwargs)

    result = await crawler.arun(
            url=url,
            extraction_strategy=strategy,
            bypass_cache=bypass_cache,
            user_agent=USER_AGENT,
            magic=True,
            page_timeout=page_timeout,
    )

    extracted_data = []
    if result.success:
        try:
            extracted_data = json.loads(result.extracted_content)
        except (json.JSONDecodeError, AttributeError):
            extracted_data = []

    # Try flare bypass if result is empty or if use_flare_bypasser is True
    if (not extracted_data or use_flare_bypasser) and PRODUCTION_MODE:
        try:
            # Use flare bypasser to get the page content
            solution = await flare_bypasser.get_page(url, max_timeout=page_timeout)
            
            if solution["status"] == "ok":
                html_result = solution["solution"]["response"]
                
                result = await crawler.aprocess_html(
                    url=url,
                    html=html_result,
                    extracted_content=None,
                    extraction_strategy=strategy,
                    config=config,
                    verbose=True,
                    bypass_cache=bypass_cache,
                    pdf_data=False,
                    screenshot=False
                )

                print(result)
                
                if result.success:
                    try:
                        extracted_data = json.loads(result.extracted_content)
                    except (json.JSONDecodeError, AttributeError):
                        pass
                        
        except Exception as e:
            logger.error(f"Flare bypass failed for {url}: {str(e)}")
            
    return extracted_data
