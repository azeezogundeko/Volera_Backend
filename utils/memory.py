import diskcache
import numpy as np
from datetime import datetime, timezone
from langgraph.store.base import BaseStore, SearchItem  # Assumed definitions
from config import MEMORY_CACHE_DIR

from langchain_community.embeddings.fastembed import FastEmbedEmbeddings


class DiskCacheStore(BaseStore):
    """
    A disk-backed store using diskcache for persistence.
    This store saves key-value data to disk and, if configured with an index,
    supports vector search.
    """
    def __init__(self, cache_dir: str = '/tmp/diskcache', index: dict = None) -> None:
        # Main cache for items
        self.cache = diskcache.Cache(cache_dir)
        # Separate cache for vector embeddings; stored under a related directory.
        self.vector_cache = diskcache.Cache(f"{cache_dir}_vectors")
        self.index_config = index
        if index:
            # Embedding provider must expose `embed_documents` and `embed_query`
            self.embeddings = index.get("embed")
            # List of fields to embed; default to ["text"] if not provided.
            self.fields = index.get("fields", ["text"])
        else:
            self.embeddings = None
            self.fields = []

    async def abatch(self): ...
    def batch(self): ...

    def _make_key(self, namespace: tuple[str, ...], key: str) -> str:
        """Flatten the namespace and key into a single composite key."""
        return f"{'::'.join(namespace)}::{key}"

    def put(self, namespace: tuple[str, ...], key: str, value: dict) -> None:
        """
        Save an item with metadata into the main cache.
        If vector search is enabled, compute and store embeddings for the configured fields.
        """
        composite_key = self._make_key(namespace, key)
        now = datetime.now(timezone.utc)
        item = {
            "value": value,
            "namespace": namespace,
            "key": key,
            "created_at": now,
            "updated_at": now,
        }
        self.cache[composite_key] = item
        # print(self.cache.get(composite_key), "Result of saving to dicsk")

        # If an embedding function is provided, compute and store embeddings.
        if self.index_config and self.embeddings:
            embedding_dict = {}
            # For each field, extract text and compute its embedding.
            for field in self.fields:
                text = value.get(field)
                if text:
                    # Compute embedding for the text.
                    # Here we assume embed_documents returns a list of embeddings.
                    embedding = self.embeddings.embed_documents([text])[0]
                    embedding_dict[field] = embedding
            if embedding_dict:
                self.vector_cache[composite_key] = embedding_dict
                # print(self.cache.get(composite_key), "Result of saving to embedding")
# 
    def get(self, namespace: tuple[str, ...], key: str) -> dict | None:
        """Retrieve an item by its namespace and key."""
        composite_key = self._make_key(namespace, key)
        return self.cache.get(composite_key)

    def delete(self, namespace: tuple[str, ...], key: str) -> None:
        """Remove an item (and its embedding if exists) from the caches."""
        composite_key = self._make_key(namespace, key)
        if composite_key in self.cache:
            del self.cache[composite_key]
        if composite_key in self.vector_cache:
            del self.vector_cache[composite_key]

    def search(
        self,
        namespace: tuple[str, ...],
        query: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[SearchItem]:
        """
        Perform vector similarity search within the given namespace.
        
        If the index is not configured, a basic text search (substring match) is performed.
        """
        results = []
        ns_prefix = f"{'::'.join(namespace)}::"
        print(f"Calling from memory: ", ns_prefix)

        if not (self.index_config and self.embeddings):
            # Fallback: simple text search in the stored item values.
            for composite_key in self.cache.iterkeys():
                if composite_key.startswith(ns_prefix):
                    item = self.cache[composite_key]
                    if query.lower() in str(item.get("value", {})).lower():
                        results.append(item)
            return results[offset:offset + limit]

        # Compute the embedding for the query.
        query_embedding = self.embeddings.embed_query(query)
        scored_items = []
        # Iterate over all keys in the namespace.
        for composite_key in self.cache.iterkeys():
            if composite_key.startswith(ns_prefix):
                item = self.cache[composite_key]
                embedding_dict = self.vector_cache.get(composite_key)
                if embedding_dict:
                    # For simplicity, take the maximum similarity score across all embedded fields.
                    best_score = None
                    for emb in embedding_dict.values():
                        score = _cosine_similarity(query_embedding, emb)
                        if best_score is None or score > best_score:
                            best_score = score
                    if best_score is not None:
                        scored_items.append((best_score, item))
        # Sort results in descending order of similarity.
        scored_items.sort(key=lambda x: x[0], reverse=True)
        # Apply offset and limit.
        final_items = []
        for score, item in scored_items[offset:offset + limit]:
            final_items.append(
                SearchItem(
                    namespace=item["namespace"],
                    key=item["key"],
                    value=item["value"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                    score=score,
                )
            )
        return final_items

def _cosine_similarity(query: list[float], stored: list[float]) -> float:
    """
    Compute cosine similarity between two vectors using numpy.
    """
    query_arr = np.array(query)
    stored_arr = np.array(stored)
    dot = np.dot(query_arr, stored_arr)
    norm_query = np.linalg.norm(query_arr)
    norm_stored = np.linalg.norm(stored_arr)
    if norm_query == 0 or norm_stored == 0:
        return 0.0
    return dot / (norm_query * norm_stored)

store = DiskCacheStore(
    cache_dir=MEMORY_CACHE_DIR,
    index={
        "embed": FastEmbedEmbeddings()
    }
)