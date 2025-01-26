import asyncio
import time
from itertools import chain
# from cachetools import TTLCache
from typing import List, Optional, Any
from diskcache import FanoutCache
# from fastembed import TextEmbedding

import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS

# from langchain.storage import LocalFileStore

from utils.logging import logger
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings


# class DiskCacheDB:
#     _instance = None  
#     _lock = asyncio.Lock() 

#     def __new__(cls, *args, **kwargs):
#         """
#         Override the __new__ method to implement the singleton pattern.
#         """
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#         return cls._instance

#     def __init__(self):
#         """
#         Initialize the cache.
#         Prevent reinitialization for the singleton instance.
#         """
#         if not hasattr(self, "cache"):
#             self.cache = None  # Placeholder for cache
#             self.lock = asyncio.Lock()  # Instance-level lock

#     async def initialize(self, max_size=100, ttl=600):
#         """
#         Asynchronous initialization method for the cache.
#         :param max_size: Maximum number of items in the cache.
#         :param ttl: Time-to-live for each item in seconds.
#         """
#         async with DiskCacheDB._lock:  # Thread-safe initialization
#             if self.cache is None:  # Only initialize once
#                 self.cache = TTLCache(maxsize=max_size, ttl=ttl)

#     async def set(self, key, value):
#         """
#         Add an item to the cache.
#         :param key: Key to store the item under.
#         :param value: Value to store in the cache.
#         """
#         async with self.lock:
#             self.cache[key] = value

#     async def get(self, key):
#         """
#         Retrieve an item from the cache.
#         :param key: Key of the item to retrieve.
#         :return: The cached value or None if the key doesn't exist or has expired.
#         """
#         async with self.lock:
#             return self.cache.get(key, None)

#     async def delete(self, key):
#         """
#         Remove an item from the cache.
#         :param key: Key of the item to delete.
#         """
#         async with self.lock:
#             if key in self.cache:
#                 del self.cache[key]

#     async def clear(self):
#         """
#         Clear all items from the cache.
#         """
#         async with self.lock:
#             self.cache.clear()

#     def __repr__(self):
#         size = len(self.cache) if self.cache else 0
#         ttl = self.cache.ttl if self.cache else "N/A"
#         return f"AsyncCacheDB(size={size}, ttl={ttl})"


class VectorStore:
    _instance = None


    def __new__(cls, *args, **kwargs):
        """
        Override the __new__ method to implement the singleton pattern.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self, ttl: int = 3600):  # Default TTL is 1 hour
        """
        Initialize the VectorStore with a FAISS index and TTL for cached queries.
        """
        if not hasattr(self, "vectorstore"):
            self.vectorstore = None
        
        self.ttl = ttl  # Time-to-Live in seconds
        self.expiration_times = {}  # Map key -> expiration timestamp


    async def initialize(self):
        """
        Asynchronous initialization for the disk cache.
        :param directory: Path to the directory where cache files will be stored.
        :param size_limit: Maximum size of the cache in bytes (None for unlimited).
        """

        index = faiss.IndexFlatL2(len(FastEmbedEmbeddings().embed_query("hello world")))

        self.vectorstore = FAISS(
            embedding_function=FastEmbedEmbeddings(),
            docstore=InMemoryDocstore(),
            index=index,
            index_to_docstore_id={},
        )


    async def query(self, query: str, k=4, score_threshold=0.8) -> List[dict]:
        """
        Perform a similarity search and return results above the score threshold.
        """
        await self._remove_expired()  # Cleanup expired entries before querying
        docs_and_similarities = await self.vectorstore.asimilarity_search_with_relevance_scores(query, k=k)

        docs_and_similarities = [
            (doc, similarity)
            for doc, similarity in docs_and_similarities
            if similarity >= score_threshold
        ]

        if not docs_and_similarities:
            return None

        logger.info(f"Returning results from cache {len(docs_and_similarities)}")
        

        return list(chain.from_iterable(doc.metadata["result"] for doc, _ in docs_and_similarities))

    async def add(self, key: str | int, query: str, result: dict | List[dict]):
        """
        Cache a query and its result with an expiration timestamp.
        """
        expiration_time = time.time() + self.ttl
        self.expiration_times[key] = expiration_time
        return await self.vectorstore.aadd_texts([query], ids=[key], metadatas=[dict(result=result, query=query)])


    async def delete(self, keys: Optional[List[str]] = None, **kwargs: Any):
        """
        Delete specified keys or perform cleanup based on additional criteria.
        """
        if keys:
            for key in keys:
                self.expiration_times.pop(key, None)
        return await self.vectorstore.adelete(keys)

    async def _remove_expired(self):
        """
        Remove expired items from the vectorstore.
        """
        current_time = time.time()
        expired_keys = [key for key, expiration in self.expiration_times.items() if expiration < current_time]

        if expired_keys:
            for key in expired_keys:
                self.expiration_times.pop(key, None)
            await self.vectorstore.adelete(expired_keys)



class DiskCacheDB:
    _instance = None  # Class-level variable to hold the singleton instance
    _lock = asyncio.Lock()  # Class-level lock for thread-safe initialization

    def __new__(cls, *args, **kwargs):
        """
        Override the __new__ method to implement the singleton pattern.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ttl=3600, cache_dir="cache", size_limit=None):
        """
        Initialize the cache.
        Prevent reinitialization for the singleton instance.
        """
        self.ttl = ttl  
        self.cache_dir=cache_dir
       
        # self.size_limit=size_limit
        if not hasattr(self, "cache"):
            self.cache = None  # Placeholder for the disk cache

    

    async def initialize(self):
        """
        Asynchronous initialization for the disk cache.
        :param directory: Path to the directory where cache files will be stored.
        :param size_limit: Maximum size of the cache in bytes (None for unlimited).
        """
        async with DiskCacheDB._lock:  # Thread-safe initialization
            if self.cache is None:  # Only initialize once
                self.cache = FanoutCache(directory=self.cache_dir)

    async def set(self, key, value, tag):
        """
        Add an item to the cache.
        :param key: Key to store the item under.
        :param value: Value to store in the cache.
        """
        if self.cache is None:
            raise Exception("Cache is not initialized. Call `initialize` first.")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.cache.set(key+tag, value, self.ttl))

    async def get(self, key, tag):
        """
        Retrieve an item from the cache.
        :param key: Key of the item to retrieve.
        :return: The cached value or None if the key doesn't exist.
        """
        if self.cache is None:
            raise Exception("Cache is not initialized. Call `initialize` first.")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: self.cache.get(key+tag))
        
        # Check if the result is a tuple
        if isinstance(result, tuple) and len(result) > 0:
            product_dict = result[0]  # Extract the first element
            if isinstance(product_dict, dict):
                return product_dict  # Return the dictionary

            elif  isinstance(product_dict, list):
                return product_dict

            else:
                return None
        else:
            # Handle the case where result is not a tuple
            return result

    async def delete(self, key):
        """
        Remove an item from the cache.
        :param key: Key of the item to delete.
        """
        if self.cache is None:
            raise Exception("Cache is not initialized. Call `initialize` first.")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.cache.delete(key))

    def close(self):
        return self.cache.close()

    async def get_stats(self):
        """
        Retrieve statistics about the cache.
        :return: A dictionary containing cache statistics.
        """
        if self.cache is None:
            raise Exception("Cache is not initialized. Call `initialize` first.")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: {
                "items": len(self.cache),
                "size": self.cache.volume(),  # Size of the cache in bytes
                "directory": self.cache.directory,
            },
        )

    async def clear(self):
        """
        Clear all items from the cache.
        """
        if self.cache is None:
            raise Exception("Cache is not initialized. Call `initialize` first.")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.cache.clear)

    def __repr__(self):
        size = len(self.cache) if self.cache else 0
        return f"DiskCacheDB(size={size})"
