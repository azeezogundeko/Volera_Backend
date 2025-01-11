import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Literal, Optional, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from utils.logging import logger

class ProductDBManager:
    def __init__(self, db_path: str = "product_cache.db", cleanup_interval: int = 3600, max_workers: int = 4):
        """
        Initialize the ProductDBManager.
        
        Args:
            db_path: Path to SQLite database file
            cleanup_interval: Interval in seconds for cache cleanup (default: 1 hour)
            max_workers: Maximum number of thread pool workers
        """
        self.db_path = db_path
        self.cleanup_interval = cleanup_interval
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._loop = asyncio.get_event_loop()
        self._setup_database()
        self._start_cleanup_task()

    async def _run_in_executor(self, func, *args, **kwargs):
        """Run a function in the thread pool executor."""
        return await self._loop.run_in_executor(
            self._executor,
            partial(func, *args, **kwargs)
        )

    def _setup_database(self):
        """Create necessary database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Drop existing table if it exists
            # cursor.execute("DROP TABLE IF EXISTS products")
            
            # Create products table for caching product data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ttl INTEGER,
                    query TEXT
                )
            """)
            
            # Create index on timestamp for faster cleanup
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON products(timestamp)
            """)
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper settings."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _cache_product_sync(
        self,
        product_id: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        ttl: Optional[int] = None,
        type: Literal["list", "detail"]="detail",
        query: Optional[str] = None
    ) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                compound_id = f"{product_id}/{type}"
                cursor.execute("""
                    INSERT OR REPLACE INTO products 
                    (product_id, data, timestamp, ttl, query)
                    VALUES (?, ?, datetime('now'), ?, ?)
                """, (
                    compound_id,
                    json.dumps(data),
                    ttl,
                    query
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error caching product {product_id}: {str(e)}")
            return False

    async def cache_product(
        self,
        product_id: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        ttl: Optional[int] = None,
        type: str = "detail",
        query: Optional[str] = None
    ) -> bool:
        """
        Asynchronously cache product data in the database.
        """
        return await self._run_in_executor(
            self._cache_product_sync,
            product_id,
            data,
            ttl,
            type,
            query
        )

    def _get_cached_product_sync(
        self,
        product_id: str,
        type: Literal["list", "detail"] = "detail"
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                compound_id = f"{product_id}/{type}"
                
                cursor.execute("""
                    SELECT data, datetime(timestamp) as timestamp, ttl 
                    FROM products 
                    WHERE product_id = ?
                """, [compound_id])
                
                result = cursor.fetchone()
                
                if not result:
                    print(f"No result found for product_id: {product_id}")
                    return None
                
                # Check if cache is expired
                timestamp = datetime.strptime(result['timestamp'], '%Y-%m-%d %H:%M:%S')
                ttl = result['ttl']
                
                print(f"Found product. Timestamp: {timestamp}, TTL: {ttl}")
                
                if ttl is not None:
                    expiry_time = timestamp + timedelta(seconds=ttl)
                    current_time = datetime.utcnow()  # Use UTC time
                    if current_time > expiry_time:
                        print(f"Cache expired. Current time (UTC): {current_time}, Expiry time: {expiry_time}")
                        return None
                    print(f"Cache valid. Expires in {expiry_time - current_time}")
                
                return json.loads(result['data'])
                
        except Exception as e:
            logger.error(f"Error retrieving cached product {product_id}: {str(e)}")
            return None

    async def get_cached_product(
        self,
        product_id: str,
        type: str = "detail",
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        Asynchronously retrieve cached product data.
        """
        return await self._run_in_executor(
            self._get_cached_product_sync,
            product_id,
            type
        )

    def _find_similar_cached_query_sync(
        self,
        query: str,
        similarity_threshold: float = 0.8
    ) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT product_id, data, query, timestamp, ttl
                    FROM products
                    WHERE query IS NOT NULL
                """)
                
                results = cursor.fetchall()
                best_match = None
                highest_similarity = 0.0
                
                for result in results:
                    # Check if cache is expired
                    timestamp = datetime.fromisoformat(result['timestamp'])
                    ttl = result['ttl']
                    
                    if ttl is not None:
                        if datetime.now() > timestamp + timedelta(seconds=ttl):
                            continue
                    
                    cached_query = result['query']
                    similarity = self._compute_similarity(query, cached_query)
                    
                    if similarity > highest_similarity and similarity >= similarity_threshold:
                        highest_similarity = similarity
                        best_match = result
                
                if best_match:
                    return json.loads(best_match['data'])
                    
                return None
                
        except Exception as e:
            logger.error(f"Error finding similar cached query: {str(e)}")
            return None

    async def find_similar_cached_query(
        self,
        query: str,
        similarity_threshold: float = 0.8
    ) -> Optional[Dict[str, Any]]:
        """
        Asynchronously find cached results for similar queries.
        """
        return await self._run_in_executor(
            self._find_similar_cached_query_sync,
            query,
            similarity_threshold
        )

    def _compute_similarity(self, query1: str, query2: str) -> float:
        """Compute similarity between two queries."""
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def _remove_expired_cache_sync(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM products 
                    WHERE ttl IS NOT NULL 
                    AND datetime(timestamp, '+' || ttl || ' seconds') < datetime('now')
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Error removing expired cache: {str(e)}")

    async def remove_expired_cache(self):
        """Asynchronously remove expired cache entries."""
        await self._run_in_executor(self._remove_expired_cache_sync)

    def _start_cleanup_task(self):
        """Start background cleanup task."""
        async def cleanup_worker():
            while True:
                await self.remove_expired_cache()
                await asyncio.sleep(self.cleanup_interval)

        asyncio.create_task(cleanup_worker())

    def _clear_cache_sync(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products")
                conn.commit()
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")

    async def clear_cache(self):
        """Asynchronously clear all cached data."""
        await self._run_in_executor(self._clear_cache_sync)

    def _get_cache_stats_sync(self) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) as total FROM products")
                total = cursor.fetchone()['total']
                
                cursor.execute("""
                    SELECT COUNT(*) as expired
                    FROM products 
                    WHERE ttl IS NOT NULL 
                    AND datetime(timestamp, '+' || ttl || ' seconds') < datetime('now')
                """)
                expired = cursor.fetchone()['expired']
                
                return {
                    "total_entries": total,
                    "expired_entries": expired,
                    "database_size_bytes": Path(self.db_path).stat().st_size
                }
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Asynchronously get cache statistics."""
        return await self._run_in_executor(self._get_cache_stats_sync)

    async def close(self):
        """Close the database manager and cleanup resources."""
        self._executor.shutdown(wait=True) 