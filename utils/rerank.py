import typing
import asyncio
import logging

# from langchain import retrievers
from config import ApiKeyConfig
from dataclasses import dataclass
from typing import List


# from .prompt import information_extractor_prompt
from .decorator import async_retry
from .logging import logger

import httpx
from pydantic_ai import Agent   
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain.retrievers import ContextualCompressionRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from flashrank import Ranker, RerankRequest

from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain.retrievers import EnsembleRetriever
# from langchain_community.retrievers import BM25Retriever
from langchain.docstore.document import Document
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank

logger = logging.getLogger(__name__)



class WebResultDict(typing.TypedDict):
    metadata: dict
    content: str

class Docs(typing.TypedDict):
    id: str
    text: str
    metadata: dict

class ResultSchema(BaseModel):
    content: str
    valid: bool

class ProductSchema(typing.TypedDict):
    name: str
    current_price: float
    original_price: float  
    brand: str
    discount: float
    rating: float
    reviews_count: str
    product_id: str
    image: str
    currency: str
    source: str


class ProductOut(ProductSchema):
    relevance_score: float



@dataclass
class Dependencies:
    api_key = ApiKeyConfig.GEMINI_API_KEY
    http_client = httpx.AsyncClient


class ReRanker:
    def __init__(
        self, 
        cache_ttl: int = 3600, 
        chunk_size=1000, 
        chunk_overlap=200, 
        word_threshold=5000
        
        ):
        self.k = 50
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.threshold = word_threshold
        self.n_load = 20
        self.ranker = Ranker(max_length=128)
        self.embedding_model: str = "models/embedding-001"
        self.embeddings = self._load_embeddings()

        self.llm = Agent(
            result_type=ResultSchema,
            model="gemini-2.0-flash-exp",
            name="Web Content Extractor",
            # system_prompt=information_extractor_prompt,
            deps_type=Dependencies,
        )

    def _load_embeddings(self):
        return GoogleGenerativeAIEmbeddings(
            model=self.embedding_model, 
            google_api_key=ApiKeyConfig.GEMINI_API_KEY
            )

    async def load_contents(self, k, documents: typing.List[Document]):
        logger.info(f"Number of documents to load: {len(documents)}")
        try:
            vectorstore = await asyncio.to_thread(
                FAISS.from_documents,
                documents=documents,
                embedding=self.embeddings
            )
            logger.info("FAISS vectorstore created successfully.")
            return vectorstore.as_retriever(search_kwargs={"k": k})
        except Exception as e:
            logger.error(f"Error creating FAISS vectorstore: {e}")
            raise

    async def _reranker(
        self, 
        query: str, 
        retriever, 
        k: int = 200,
        mode: typing.Literal["fast", "balanced", "quality"] = "fast", 
        ) -> typing.List[Document]:
        """Rerank results based on relevance."""
        model = "ms-marco-TinyBERT-L-2-v2"  # Default to fast mode model
        if mode == "balanced":
            model = "ms-marco-MiniLM-L-12-v2"
        elif mode == "quality":
            k=k+5
            # model = "rank-T5-flan"
        
        compressor = FlashrankRerank(model=model, top_n=k)
        compressor_retriever = ContextualCompressionRetriever(
            base_retriever=retriever,
            base_compressor=compressor
        )
        return await compressor_retriever.ainvoke(query, k=k)


    def to_document(self, results: List[ProductSchema]) -> List[Document]:
        docs = [
            Docs(text=result["name"], metadata=result, id=id)
            for id, result in enumerate(results)
        ]
        return docs


    async def rerank(self, query: str, results: List[ProductSchema], k=20) -> List[ProductOut]:
        docs = self.to_document(results)
        rerankrequest = RerankRequest(query=query, passages=docs)
        reranked = self.ranker.rerank(rerankrequest)

        # retriever = await self.load_contents(k, docs)
        # print(f"Length pf results {len(docs)}")
        # reranked = await self._reranker(retriever=retriever, query=query, k=k)

        print(f"Length of reranked: {len(reranked)}")   

        products = [
            ProductOut(
                **{
                    **rerank["metadata"],
                    'relevance_score': float(rerank.get('score', 0.0))
                }
            )
            for rerank in reranked
        ]
        return products



    def clean_metadata(self, metadata: dict) -> dict:
        """
        Recursively convert all numpy.float32 to float in a metadata dictionary.
        """
        import numpy as np
        for key, value in metadata.items():
            if isinstance(value, dict):
                metadata[key] = clean_metadata(value)
            elif isinstance(value, np.float32):
                metadata[key] = float(value)
        return metadata

    def chunk_content(self, search_results: typing.List[Document]):
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=self.chunk_size,
        chunk_overlap=self.chunk_overlap
        )
        splits = splitter.split_documents(search_results)
        return splits


    async def extract_content(self, search_results: typing.List[Document])-> typing.List[WebResultDict]:
        results = []
        for search_result in search_results:
            web_content = f"""
                Web Content: {search_result.page_content}
                """
            try:
                content = await self.llm.run(web_content)
                data = content.data
                if data.valid is False:
                    continue

                results.append(
                    WebResultDict(metadata=search_result.metadata, content=data.content
                    )
                )
   
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error extracting content: {e}")
                continue

        return results
