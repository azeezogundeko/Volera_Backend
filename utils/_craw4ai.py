from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import (
    LLMExtractionStrategy,
    JsonCssExtractionStrategy,
    CosineStrategy
)

class CrawlerManager:
    _instance = None
    _crawler = None
    
    @classmethod
    async def initialize(cls):
        """Initialize the crawler instance if it doesn't exist"""
        if cls._crawler is None:
            cls._crawler = AsyncWebCrawler(verbose=True)
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
