from typing import List, Optional
import re

from config import SEARCH_CACHE_DIR
from utils.logging import logger
from diskcache import Cache

class SearchCacheManager:

    def __init__(self):
        self.cache = Cache(directory=str(SEARCH_CACHE_DIR))
        self.ttl = 30*24*60*60

    def add_search_query(self, query: str):
        """Add a search query to the cache"""
        try:
            query = query.lower().strip()
            if not query:
                return
        
            # Get existing queries
            existing_queries = self.cache.get(query[0]) or []
            if not isinstance(existing_queries, list):
                existing_queries = []

            # Add new query if not exists
            if query not in existing_queries:
                existing_queries.append(query)
                self.cache.set(query[0], existing_queries, expire=self.ttl)

        except Exception as e:
            logger.error(f"Failed to add search query to cache: {str(e)}")

    def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on query prefix"""
        if not query:
            return []

        query = query.lower().strip()
        first_char = query[0]

        # Get all queries starting with the same letter
        cached_queries = self.cache.get(first_char) or []
        if not isinstance(cached_queries, list):
            return []

        # Filter queries that match the input prefix
        pattern = re.compile(f"^{re.escape(query)}")
        suggestions = [
            q for q in cached_queries 
            if pattern.match(q)
        ]

        # Sort by length (shorter suggestions first) and limit results
        suggestions.sort(key=len)
        return suggestions[:limit]

# Create a singleton instance
search_cache_manager = SearchCacheManager() 