"""
MongoDB Vector Store Implementation
Stores document embeddings in MongoDB with vector similarity search support.
Compatible with MongoDB Atlas Vector Search or local MongoDB.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid

from config import MONGODB_URL, MONGODB_DATABASE


class MongoDBVectorStore(VectorStore):
    """
    MongoDB-based vector store for LangChain.
    
    Stores documents and their embeddings in MongoDB with support for:
    - Vector similarity search (cosine similarity)
    - Metadata filtering
    - Async operations
    
    For production use with large datasets, consider MongoDB Atlas Vector Search.
    """
    
    def __init__(
        self,
        collection_name: str = "vector_store",
        embedding_function: Optional[Embeddings] = None,
        mongodb_url: str = MONGODB_URL,
        database_name: str = MONGODB_DATABASE,
    ):
        """
        Initialize MongoDB Vector Store.
        
        Args:
            collection_name: Name of the MongoDB collection
            embedding_function: LangChain embeddings instance
            mongodb_url: MongoDB connection URL
            database_name: MongoDB database name
        """
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        
        # Synchronous client for VectorStore interface
        self.client = MongoClient(mongodb_url)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        
        # Create indexes for better performance
        self._ensure_indexes()
        
        print(f"[OK] MongoDB VectorStore initialized: {database_name}.{collection_name}")
    
    def _ensure_indexes(self):
        """Create necessary indexes for efficient querying."""
        try:
            # Index on metadata fields for filtering
            self.collection.create_index([("metadata.source", 1)])
            self.collection.create_index([("created_at", -1)])
        except Exception as e:
            print(f"[WARNING] Could not create indexes: {e}")
    
    @property
    def embeddings(self) -> Optional[Embeddings]:
        """Return the embedding function."""
        return self.embedding_function
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """
        Add texts to the vector store.
        
        Args:
            texts: List of text strings to add
            metadatas: Optional list of metadata dicts
            
        Returns:
            List of document IDs
        """
        if not self.embedding_function:
            raise ValueError("Embedding function is required")
        
        # Generate embeddings
        embeddings = self.embedding_function.embed_documents(texts)
        
        # Prepare documents
        documents = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            doc = {
                "text": text,
                "embedding": embedding,
                "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                "created_at": datetime.utcnow(),
            }
            documents.append(doc)
        
        # Insert into MongoDB
        result = self.collection.insert_many(documents)
        doc_ids = [str(id) for id in result.inserted_ids]
        
        print(f"[OK] Added {len(doc_ids)} documents to MongoDB vector store")
        return doc_ids
    
    def add_documents(
        self,
        documents: List[Document],
        **kwargs: Any,
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            List of document IDs
        """
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        return self.add_texts(texts, metadatas, **kwargs)
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """
        Perform similarity search.
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of similar documents
        """
        if not self.embedding_function:
            raise ValueError("Embedding function is required")
        
        # Generate query embedding
        query_embedding = self.embedding_function.embed_query(query)
        
        # Build MongoDB query
        mongo_filter = filter if filter else {}
        
        # Fetch all documents (for cosine similarity calculation)
        # For production with large datasets, use MongoDB Atlas Vector Search
        cursor = self.collection.find(mongo_filter)
        
        # Calculate similarities
        results = []
        for doc in cursor:
            similarity = self._cosine_similarity(query_embedding, doc["embedding"])
            results.append((doc, similarity))
        
        # Sort by similarity and take top k
        results.sort(key=lambda x: x[1], reverse=True)
        top_results = results[:k]
        
        # Convert to LangChain documents
        documents = []
        for doc, score in top_results:
            documents.append(
                Document(
                    page_content=doc["text"],
                    metadata={
                        **doc["metadata"],
                        "score": score,
                        "_id": str(doc["_id"]),
                    }
                )
            )
        
        return documents
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """
        Perform similarity search with scores.
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of (document, score) tuples
        """
        if not self.embedding_function:
            raise ValueError("Embedding function is required")
        
        # Generate query embedding
        query_embedding = self.embedding_function.embed_query(query)
        
        # Build MongoDB query
        mongo_filter = filter if filter else {}
        
        # Fetch all documents
        cursor = self.collection.find(mongo_filter)
        
        # Calculate similarities
        results = []
        for doc in cursor:
            similarity = self._cosine_similarity(query_embedding, doc["embedding"])
            results.append((doc, similarity))
        
        # Sort by similarity and take top k
        results.sort(key=lambda x: x[1], reverse=True)
        top_results = results[:k]
        
        # Convert to LangChain documents with scores
        documents_with_scores = []
        for doc, score in top_results:
            document = Document(
                page_content=doc["text"],
                metadata={
                    **doc["metadata"],
                    "_id": str(doc["_id"]),
                }
            )
            documents_with_scores.append((document, score))
        
        return documents_with_scores
    
    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        collection_name: str = "vector_store",
        **kwargs: Any,
    ) -> "MongoDBVectorStore":
        """
        Create a vector store from texts.
        
        Args:
            texts: List of texts
            embedding: Embeddings instance
            metadatas: Optional metadata
            collection_name: Collection name
            
        Returns:
            MongoDBVectorStore instance
        """
        store = cls(
            collection_name=collection_name,
            embedding_function=embedding,
            **kwargs
        )
        store.add_texts(texts, metadatas)
        return store
    
    @classmethod
    def from_documents(
        cls,
        documents: List[Document],
        embedding: Embeddings,
        collection_name: str = "vector_store",
        **kwargs: Any,
    ) -> "MongoDBVectorStore":
        """
        Create a vector store from documents.
        
        Args:
            documents: List of Document objects
            embedding: Embeddings instance
            collection_name: Collection name
            
        Returns:
            MongoDBVectorStore instance
        """
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        return cls.from_texts(texts, embedding, metadatas, collection_name, **kwargs)
    
    def delete(self, ids: Optional[List[str]] = None, **kwargs: Any) -> Optional[bool]:
        """
        Delete documents by IDs.
        
        Args:
            ids: List of document IDs to delete
            
        Returns:
            True if successful
        """
        if not ids:
            return False
        
        from bson import ObjectId
        object_ids = [ObjectId(id) for id in ids if ObjectId.is_valid(id)]
        
        result = self.collection.delete_many({"_id": {"$in": object_ids}})
        print(f"[OK] Deleted {result.deleted_count} documents from MongoDB vector store")
        return True
    
    def clear(self) -> None:
        """Clear all documents from the collection."""
        result = self.collection.delete_many({})
        print(f"[OK] Cleared {result.deleted_count} documents from MongoDB vector store")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        count = self.collection.count_documents({})
        
        # Get sample document to check embedding dimension
        sample = self.collection.find_one()
        embedding_dim = len(sample["embedding"]) if sample and "embedding" in sample else 0
        
        return {
            "total_documents": count,
            "embedding_dimension": embedding_dim,
            "collection_name": self.collection_name,
            "database_name": self.database_name,
        }
    
    def as_retriever(self, **kwargs: Any):
        """
        Return a retriever interface.
        
        Args:
            **kwargs: Arguments to pass to the retriever
            
        Returns:
            VectorStoreRetriever instance
        """
        from langchain_core.vectorstores import VectorStoreRetriever
        return VectorStoreRetriever(vectorstore=self, **kwargs)
    
    def __del__(self):
        """Close MongoDB connection."""
        try:
            if hasattr(self, 'client') and self.client is not None:
                self.client.close()
        except (TypeError, AttributeError):
            # Ignore errors during Python shutdown
            pass


# Async version for better performance
class AsyncMongoDBVectorStore:
    """
    Async MongoDB Vector Store for high-performance operations.
    
    Use this for async/await contexts and better concurrency.
    """
    
    def __init__(
        self,
        collection_name: str = "vector_store",
        embedding_function: Optional[Embeddings] = None,
        mongodb_url: str = MONGODB_URL,
        database_name: str = MONGODB_DATABASE,
    ):
        """Initialize Async MongoDB Vector Store."""
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        
        # Async client
        self.client: Optional[AsyncIOMotorClient] = None
        self.collection: Optional[AsyncIOMotorCollection] = None
    
    async def connect(self):
        """Connect to MongoDB."""
        self.client = AsyncIOMotorClient(self.mongodb_url)
        self.db = self.client[self.database_name]
        self.collection = self.db[self.collection_name]
        
        # Create indexes
        await self.collection.create_index([("metadata.source", 1)])
        await self.collection.create_index([("created_at", -1)])
        
        print(f"[OK] Async MongoDB VectorStore connected: {self.database_name}.{self.collection_name}")
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents asynchronously."""
        if not self.embedding_function:
            raise ValueError("Embedding function is required")
        
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Generate embeddings
        embeddings = self.embedding_function.embed_documents(texts)
        
        # Prepare documents
        docs_to_insert = []
        for text, embedding, metadata in zip(texts, embeddings, metadatas):
            docs_to_insert.append({
                "text": text,
                "embedding": embedding,
                "metadata": metadata,
                "created_at": datetime.utcnow(),
            })
        
        # Insert into MongoDB
        result = await self.collection.insert_many(docs_to_insert)
        doc_ids = [str(id) for id in result.inserted_ids]
        
        print(f"[OK] Added {len(doc_ids)} documents to MongoDB vector store (async)")
        return doc_ids
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            print("[OK] Disconnected from MongoDB")


# Helper function to get MongoDB vector store instance
def get_mongodb_vectorstore(
    collection_name: str = "cloudfuze_vectorstore",
    embedding_function: Optional[Embeddings] = None,
) -> MongoDBVectorStore:
    """
    Get a MongoDB vector store instance.
    
    Args:
        collection_name: Name of the collection
        embedding_function: Embeddings instance
        
    Returns:
        MongoDBVectorStore instance
    """
    return MongoDBVectorStore(
        collection_name=collection_name,
        embedding_function=embedding_function,
    )



