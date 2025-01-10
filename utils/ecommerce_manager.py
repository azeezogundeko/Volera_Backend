import re
import hashlib
from collections import defaultdict
from typing import Dict, Any, Optional, List, Union, Literal
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from pydantic import BaseModel

from .ecommerce.base import EcommerceIntegration
from utils.logging import logger


class CacheEntry(BaseModel):
    data: Union[Dict[str, Any], List[Dict[str, Any]]]
    timestamp: datetime
    type: Literal["list", "detail"]
    product_id: str
    ttl: Optional[int] = None
    query: Optional[str] = None  # Store original query for similarity check

class EcommerceManager:
    def __init__(self, cache_duration: timedelta = timedelta(hours=24), similarity_threshold: float = 0.8):
        self._integrations: Dict[str, EcommerceIntegration] = {}
        self._cache: Dict[str, CacheEntry] = {}
        self.cache_duration = cache_duration
        self.similarity_threshold = similarity_threshold
        
        # Register default integrations
        self._register_default_integrations()

    def _register_default_integrations(self):
        """Register default website integrations."""
        from .ecommerce_integrations.jumia import JumiaIntegration
        from .ecommerce_integrations.jiji import JijiIntegration
        from .ecommerce_integrations.konga import KongaIntegration
        
        # Register each integration
        for integration_class in [JumiaIntegration, JijiIntegration, KongaIntegration]:
            integration = integration_class()
            self.register_integration(integration)

    def register_integration(self, integration: EcommerceIntegration) -> None:
        """Register a new e-commerce integration."""
        self._integrations[integration.name] = integration

    def get_integration_for_url(self, url: str) -> Optional[EcommerceIntegration]:
        """Get the registered integration for a given URL."""
        for integration in self._integrations.values():
            if integration.matches_url(url):
                return integration
        return None

    def generate_product_id(self, url: str) -> str:
        """Generate a unique product ID from a URL."""
        return hashlib.sha256(url.encode()).hexdigest()

    def is_cache_valid(self, entry: CacheEntry) -> bool:
        """Check if a cache entry is still valid based on TTL or default cache duration."""
        now = datetime.now()
        if entry.ttl is not None:
            return (now - entry.timestamp) <= timedelta(seconds=entry.ttl)
        return (now - entry.timestamp) <= self.cache_duration

    def _normalize_query(self, query: str) -> str:
        """Normalize query for better comparison."""
        # Convert to lowercase and remove extra spaces
        query = " ".join(query.lower().split())
        # Remove special characters
        query = re.sub(r'[^\w\s]', '', query)
        return query

    def _compute_word_similarity(self, query1: str, query2: str) -> float:
        """Compute similarity between two queries based on word overlap."""
        # Normalize queries
        query1 = self._normalize_query(query1)
        query2 = self._normalize_query(query2)
        
        # Split into words
        words1 = set(query1.split())
        words2 = set(query2.split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
            
        # Calculate sequence similarity for additional precision
        sequence_similarity = SequenceMatcher(None, query1, query2).ratio()
        
        # Combine both metrics (give more weight to word overlap)
        word_similarity = intersection / union
        combined_similarity = (word_similarity * 0.7) + (sequence_similarity * 0.3)
        
        return combined_similarity

    def _find_similar_cached_query(self, query: str, type: Literal["list", "detail"]) -> Optional[CacheEntry]:
        """Find a similar query in cache."""
        best_match = None
        highest_similarity = 0.0

        for entry in self._cache.values():
            if entry.type != type or not entry.query:
                continue
                
            if not self.is_cache_valid(entry):
                continue

            similarity = self._compute_word_similarity(query, entry.query)
            if similarity > highest_similarity and similarity >= self.similarity_threshold:
                highest_similarity = similarity
                best_match = entry

        return best_match

    def get_cached_data(self, product_url: str = None, query: str = None, type: Literal["list", "detail"] = "list") -> Optional[Dict[str, Any]]:
        """Get cached data if it exists and is not expired."""
        if type == "list":
            # For list type, try to find similar queries
            if query:
                similar_entry = self._find_similar_cached_query(query, type)
                if similar_entry:
                    return similar_entry.data
            else:
                return None

        # For detail type or if no similar query found, use exact match
        if product_url:
            product_id = self.generate_product_id(product_url)
            if product_id in self._cache:
                entry = self._cache[product_id]
                if self.is_cache_valid(entry) and entry.type == type:
                    return entry.data
                del self._cache[product_id]
        return None

    def cache_data(
        self,
        url_or_query: str,
        type: Literal["list", "detail"],
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        ttl: Optional[int] = None
    ) -> None:
        """Cache data with optional TTL."""
        if not data:
            return
            
        product_id = self.generate_product_id(url_or_query)
        try:
            self._cache[product_id] = CacheEntry(
                data=data,
                type=type,
                timestamp=datetime.now(),
                product_id=product_id,
                ttl=ttl,
                query=url_or_query if type == "list" else None  # Store query only for list type
            )
        except Exception as e:
            logger.error(f"Failed to cache data for URL/query {url_or_query}: {str(e)}")

    def set_ttl(self, url: str, ttl: int) -> bool:
        """Set or update TTL for a cached entry."""
        product_id = self.generate_product_id(url)
        if product_id in self._cache:
            entry = self._cache[product_id]
            self._cache[product_id] = CacheEntry(
                data=entry.data,
                type=entry.type,
                timestamp=entry.timestamp,
                product_id=entry.product_id,
                ttl=ttl
            )
            return True
        return False

    def _preprocess_url(self, url: str) -> str:
        """Preprocess URL before fetching data."""
        if "?" in url and any(integration.matches_url(url) for integration in self._integrations.values()):
            url = url.split("?")[0]
        return url.strip()

    async def process_url(
        self,
        url: str,
        ttl: Optional[int] = 3600,
        bypass_cache: bool = False
    ) -> List[Dict[str, Any]]:
        """Process a single URL and return extracted products."""
        try:
            processed_url = self._preprocess_url(url)
            logger.info(f"Processing URL: {processed_url}")
            
            # Check cache first
            if not bypass_cache:
                cached = self.get_cached_data(processed_url, type="list")
                if cached:
                    return cached if isinstance(cached, list) else [cached]
            
            # Get integration
            integration = self.get_integration_for_url(processed_url)
            if not integration:
                logger.warning(f"No integration found for URL: {processed_url}")
                return []
            
            # Get product list
            products = await integration.get_product_list(
                url=processed_url,
                bypass_cache=bypass_cache
            )
            
            if products:
                self.cache_data(processed_url, type="list", data=products, ttl=ttl)
            
            return products
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            return []

    async def get_product_detail(
        self,
        product_url: str,
        bypass_cache: bool = False,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get detailed product information from a URL."""
        if not bypass_cache:

            cached = self.get_cached_data(product_url, type="detail")
            if cached:
                return cached

        integration = self.get_integration_for_url(product_url)
        if not integration:
            raise ValueError(f"No integration found for product URL: {product_url}")
        
        product = await integration.get_product_detail(
            url=product_url,
            bypass_cache=bypass_cache
        )

        if product:
            self.cache_data(product_url, type="detail", data=product, ttl=ttl)
            return product

        return {}

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()

    def remove_expired_cache(self) -> None:
        """Remove all expired cache entries."""
        expired_keys = [
            product_id for product_id, entry in self._cache.items()
            if not self.is_cache_valid(entry)
        ]
        for key in expired_keys:
            del self._cache[key]

    def get_cache_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get information about a cached entry."""
        product_id = self.generate_product_id(url)
        if product_id in self._cache:
            entry = self._cache[product_id]
            now = datetime.now()
            time_elapsed = (now - entry.timestamp).total_seconds()
            
            if entry.ttl is not None:
                time_remaining = entry.ttl - time_elapsed
            else:
                time_remaining = self.cache_duration.total_seconds() - time_elapsed
                
            return {
                "product_id": entry.product_id,
                "cached_at": entry.timestamp,
                "ttl": entry.ttl,
                "time_elapsed": time_elapsed,
                "time_remaining": max(0, time_remaining),
                "is_valid": self.is_cache_valid(entry)
            }
        return None 