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

from config import PRODUCTION_MODE

if PRODUCTION_MODE == "true":
    USER_QDRANT = True
else:
    USER_QDRANT = False

PRODUCTION_MODE == "false"
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
    _lock = asyncio.Lock()  # Add class-level lock for thread safety

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern to ensure a single instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ttl: int = None, use_qdrant: bool = USER_QDRANT):
        """
        Initialize the VectorStore.
        For Qdrant, default TTL is 1 week (604800 seconds).
        For FAISS, default TTL is 1 hour (3600 seconds).
        :param ttl: Optional TTL override.
        :param use_qdrant: Flag to try using Qdrant first.
        """
        if not hasattr(self, "_initialized"):
            self.vectorstore = None
            self.use_qdrant = use_qdrant
            self._initialized = False
            self._client_ready = asyncio.Event()  # Add event for client readiness

            # Set TTL based on the vector store used, unless explicitly provided.
            if ttl is not None:
                self.ttl = ttl
            else:
                self.ttl = 604800 if self.use_qdrant else 3600

            self.expiration_times = {}  # key -> expiration timestamp
            self.embedding_model = FastEmbedEmbeddings()

            # Qdrant-specific attributes
            self.qdrant_client = None
            self.collection_name = "volera_collection"

    async def _init_qdrant(self):
        """Initialize Qdrant client with retry logic"""
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import VectorParams, Distance, OptimizersConfigDiff
        from qdrant_client.http import models as rest
        import time

        max_retries = 5
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to Qdrant (attempt {attempt + 1}/{max_retries})")
                client = QdrantClient(
                    host="qdrant",
                    port=6333,
                    timeout=30,  # Increased timeout for initialization
                    prefer_grpc=False  # Force HTTP
                )
                
                # Test the connection
                collections = client.get_collections()
                logger.info(f"Successfully connected to Qdrant. Available collections: {collections}")
                
                # Get vector size from embedding model
                vector_size = len(self.embedding_model.embed_query("hello world"))
                logger.info(f"Creating collection with vector size: {vector_size}")
                
                try:
                    # Try to get existing collection
                    collection_info = client.get_collection(self.collection_name)
                    logger.info(f"Found existing collection: {collection_info}")
                    
                    # Check if we need to recreate (e.g., if vector size changed)
                    if collection_info.config.params.vectors.size != vector_size:
                        logger.info("Vector size mismatch, recreating collection...")
                        client.delete_collection(self.collection_name)
                        raise ValueError("Vector size mismatch")
                        
                except Exception:
                    # Collection doesn't exist or needs recreation
                    logger.info("Creating new collection...")
                    client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=vector_size,
                            distance=Distance.COSINE
                        ),
                        optimizers_config=OptimizersConfigDiff(
                            indexing_threshold=20000,  # Increased for better performance
                            memmap_threshold=20000
                        ),
                        on_disk_payload=True  # Store payloads on disk to save memory
                    )
                    logger.info(f"Successfully created Qdrant collection: {self.collection_name}")
                
                return client
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect to Qdrant (attempt {attempt + 1}): {str(e)}")
                    await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    raise Exception(f"Failed to initialize Qdrant after {max_retries} attempts: {str(e)}")

    async def _init_faiss(self):
        """Initialize FAISS vector store"""
        try:
            vector_size = len(self.embedding_model.embed_query("hello world"))
            index = faiss.IndexFlatL2(vector_size)
            self.vectorstore = FAISS(
                embedding_function=self.embedding_model,
                docstore=InMemoryDocstore(),
                index=index,
                index_to_docstore_id={},
            )
            logger.info("Initialized FAISS index with TTL set to 1 hour.")
            return self.vectorstore
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {e}")
            raise

    async def initialize(self):
        """
        Initialize the vector store.
        First try to initialize Qdrant. If that fails, fall back to FAISS.
        """
        if self._initialized:
            await self._client_ready.wait()  # Wait for client to be ready if already initializing
            return

        async with self._lock:  # Ensure thread-safe initialization
            if self._initialized:  # Double-check pattern
                return
            
            if self.use_qdrant:
                try:
                    self.qdrant_client = await self._init_qdrant()
                    logger.info("Qdrant client initialized successfully")
                    self._initialized = True
                    self._client_ready.set()
                    return
                except Exception as e:
                    logger.error(f"Failed to initialize Qdrant: {e}. Falling back to FAISS.")
                    self.use_qdrant = False
                    self.ttl = 3600
                    self.qdrant_client = None

            # Fallback to FAISS if Qdrant initialization failed
            try:
                self.vectorstore = await self._init_faiss()
                self._initialized = True
                self._client_ready.set()
            except Exception as e:
                logger.error(f"Failed to initialize FAISS: {e}")
                raise

    async def query(self, query: str, k=4, score_threshold=0.8) -> Optional[List[dict]]:
        """
        Perform a similarity search using either Qdrant or FAISS.
        """
        await self._remove_expired()  # Clean up expired entries

        if self.use_qdrant and self.qdrant_client:
            try:
                query_vector = self.embedding_model.embed_query(query)
                results = await asyncio.to_thread(
                    self.qdrant_client.search,
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=k,
                    with_payload=True
                )
                filtered = [r for r in results if r.score and r.score >= score_threshold]
                if not filtered:
                    return None

                results_list = []
                for r in filtered:
                    if r.payload and "result" in r.payload:
                        if isinstance(r.payload["result"], list):
                            results_list.extend(r.payload["result"])
                        else:
                            results_list.append(r.payload["result"])

                logger.info(f"Returning {len(results_list)} results from Qdrant.")
                return results_list
            except Exception as e:
                logger.error(f"Failed to query Qdrant: {e}. Falling back to FAISS.")
                self.use_qdrant = False
                self.qdrant_client = None
                await self.initialize()  # Reinitialize with FAISS
                return await self.query(query, k, score_threshold)  # Retry with FAISS
        else:
            docs_and_similarities = await self.vectorstore.asimilarity_search_with_relevance_scores(query, k=k)
            docs_and_similarities = [
                (doc, similarity)
                for doc, similarity in docs_and_similarities
                if similarity >= score_threshold
            ]
            if not docs_and_similarities:
                return None

            logger.info(f"Returning {len(docs_and_similarities)} results from FAISS.")
            return list(chain.from_iterable(doc.metadata["result"] for doc, _ in docs_and_similarities))

    async def add(self, key: str | int, query: str, result: dict | List[dict]):
        """
        Add a query and its result to the vector store.
        """
        await self._client_ready.wait()  # Ensure client is ready before proceeding
        
        expiration_time = time.time() + self.ttl
        self.expiration_times[key] = expiration_time

        if self.use_qdrant and self.qdrant_client:
            try:
                from uuid import UUID, uuid5, NAMESPACE_DNS
                
                # Convert key to a valid Qdrant point ID
                try:
                    if isinstance(key, int):
                        point_id = key
                    else:
                        # Create a deterministic UUID from the key string
                        point_id = str(uuid5(NAMESPACE_DNS, str(key)))
                except Exception as e:
                    # If conversion fails, generate a new UUID
                    point_id = str(uuid5(NAMESPACE_DNS, str(time.time())))
                    logger.warning(f"Failed to convert key to UUID, using generated ID: {point_id}")

                vector = self.embedding_model.embed_query(query)
                payload = {
                    "result": result,
                    "query": query,
                    "original_key": str(key)  # Store original key in payload
                }
                
                point = {
                    "id": point_id,
                    "vector": vector,
                    "payload": payload
                }
                
                logger.info(f"Adding point with ID {point_id} to Qdrant")
                await asyncio.to_thread(
                    self.qdrant_client.upsert,
                    collection_name=self.collection_name,
                    points=[point]
                )
                logger.info(f"Added point {point_id} to Qdrant with TTL of 1 week.")
            except Exception as e:
                logger.error(f"Failed to add point to Qdrant: {e}. Falling back to FAISS.")
                self.use_qdrant = False
                self.qdrant_client = None
                # Ensure FAISS is initialized before retrying
                if not self.vectorstore:
                    await self._init_faiss()
                await self.add(key, query, result)  # Retry with FAISS
        else:
            if not self.vectorstore:
                await self._init_faiss()
            await self.vectorstore.aadd_texts(
                [query],
                ids=[key],
                metadatas=[dict(result=result, query=query)]
            )
            logger.info(f"Added point {key} to FAISS with TTL of 1 hour.")

    async def delete(self, keys: Optional[List[str]] = None, **kwargs: Any):
        """
        Delete points by key from the vector store.
        """
        if keys:
            for key in keys:
                self.expiration_times.pop(key, None)

        if self.use_qdrant:
            await asyncio.to_thread(
                self.qdrant_client.delete,
                collection_name=self.collection_name,
                points_selector={"ids": keys}
            )
            logger.info(f"Deleted points {keys} from Qdrant.")
        else:
            await self.vectorstore.adelete(keys)
            logger.info(f"Deleted points {keys} from FAISS.")

    async def _remove_expired(self):
        """
        Remove expired items from the vector store.
        """
        current_time = time.time()
        expired_keys = [key for key, expiration in self.expiration_times.items() if expiration < current_time]
        if expired_keys:
            for key in expired_keys:
                self.expiration_times.pop(key, None)
            if self.use_qdrant:
                await asyncio.to_thread(
                    self.qdrant_client.delete,
                    collection_name=self.collection_name,
                    points_selector={"ids": expired_keys}
                )
                logger.info(f"Removed expired keys {expired_keys} from Qdrant.")
            else:
                await self.vectorstore.adelete(expired_keys)
                logger.info(f"Removed expired keys {expired_keys} from FAISS.")



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
