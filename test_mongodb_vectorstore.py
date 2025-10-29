#!/usr/bin/env python3
"""
Test script for MongoDB Vector Store.
This script verifies that the MongoDB vector store is working correctly.
"""

import os
import sys
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from app.mongodb_vectorstore import MongoDBVectorStore
from config import MONGODB_VECTORSTORE_COLLECTION


def test_basic_operations():
    """Test basic vector store operations."""
    print("=" * 70)
    print("TEST 1: Basic Operations")
    print("=" * 70)
    
    # Initialize
    print("[*] Initializing MongoDB vector store...")
    embeddings = OpenAIEmbeddings()
    vectorstore = MongoDBVectorStore(
        collection_name=f"{MONGODB_VECTORSTORE_COLLECTION}_test",
        embedding_function=embeddings,
    )
    print("[OK] Vector store initialized")
    
    # Clear any existing test data
    print("[*] Clearing test data...")
    vectorstore.clear()
    
    # Test 1: Add texts
    print("\n[*] Test: Adding texts...")
    texts = [
        "CloudFuze provides cloud migration services.",
        "We help companies migrate from Slack to Microsoft Teams.",
        "Our pricing is transparent and scalable.",
    ]
    metadatas = [
        {"source": "test", "type": "service"},
        {"source": "test", "type": "migration"},
        {"source": "test", "type": "pricing"},
    ]
    
    ids = vectorstore.add_texts(texts, metadatas)
    print(f"[OK] Added {len(ids)} documents")
    
    # Test 2: Get stats
    print("\n[*] Test: Getting collection stats...")
    stats = vectorstore.get_collection_stats()
    print(f"[OK] Stats: {stats}")
    
    # Test 3: Similarity search
    print("\n[*] Test: Similarity search...")
    query = "Tell me about cloud migration"
    results = vectorstore.similarity_search(query, k=2)
    print(f"[OK] Found {len(results)} results")
    for i, doc in enumerate(results):
        print(f"  Result {i+1}: {doc.page_content[:60]}...")
    
    # Test 4: Similarity search with score
    print("\n[*] Test: Similarity search with scores...")
    results_with_scores = vectorstore.similarity_search_with_score(query, k=2)
    print(f"[OK] Found {len(results_with_scores)} results with scores")
    for i, (doc, score) in enumerate(results_with_scores):
        print(f"  Result {i+1} (score: {score:.4f}): {doc.page_content[:60]}...")
    
    # Test 5: Add documents
    print("\n[*] Test: Adding Document objects...")
    docs = [
        Document(
            page_content="CloudFuze offers enterprise solutions.",
            metadata={"source": "test", "type": "enterprise"}
        ),
    ]
    ids = vectorstore.add_documents(docs)
    print(f"[OK] Added {len(ids)} documents")
    
    # Test 6: Final stats
    print("\n[*] Test: Final collection stats...")
    stats = vectorstore.get_collection_stats()
    print(f"[OK] Final stats: {stats}")
    
    # Cleanup
    print("\n[*] Cleaning up test data...")
    vectorstore.clear()
    print("[OK] Test data cleared")
    
    print("\n✅ All basic operations tests passed!")
    return True


def test_retriever_interface():
    """Test the retriever interface."""
    print("\n" + "=" * 70)
    print("TEST 2: Retriever Interface")
    print("=" * 70)
    
    # Initialize
    print("[*] Initializing MongoDB vector store...")
    embeddings = OpenAIEmbeddings()
    vectorstore = MongoDBVectorStore(
        collection_name=f"{MONGODB_VECTORSTORE_COLLECTION}_test",
        embedding_function=embeddings,
    )
    
    # Add test data
    print("[*] Adding test data...")
    texts = [
        "CloudFuze helps with Slack to Teams migration.",
        "We offer cloud-to-cloud data migration.",
        "Enterprise customers get dedicated support.",
    ]
    vectorstore.add_texts(texts)
    
    # Test retriever
    print("\n[*] Testing retriever interface...")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    
    query = "How does migration work?"
    results = retriever.invoke(query)
    print(f"[OK] Retriever found {len(results)} results")
    for i, doc in enumerate(results):
        print(f"  Result {i+1}: {doc.page_content}")
    
    # Cleanup
    print("\n[*] Cleaning up test data...")
    vectorstore.clear()
    
    print("\n✅ Retriever interface test passed!")
    return True


def test_from_texts():
    """Test creating vector store from texts."""
    print("\n" + "=" * 70)
    print("TEST 3: Create from Texts")
    print("=" * 70)
    
    print("[*] Creating vector store from texts...")
    embeddings = OpenAIEmbeddings()
    
    texts = [
        "CloudFuze provides SaaS migration services.",
        "We support multiple cloud platforms.",
    ]
    metadatas = [
        {"source": "test"},
        {"source": "test"},
    ]
    
    vectorstore = MongoDBVectorStore.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        collection_name=f"{MONGODB_VECTORSTORE_COLLECTION}_test",
    )
    
    stats = vectorstore.get_collection_stats()
    print(f"[OK] Created vector store with {stats['total_documents']} documents")
    
    # Test search
    results = vectorstore.similarity_search("migration", k=1)
    print(f"[OK] Search returned {len(results)} results")
    
    # Cleanup
    vectorstore.clear()
    
    print("\n✅ From texts test passed!")
    return True


def test_mongodb_connection():
    """Test MongoDB connection."""
    print("\n" + "=" * 70)
    print("TEST 0: MongoDB Connection")
    print("=" * 70)
    
    try:
        from pymongo import MongoClient
        from config import MONGODB_URL
        
        print(f"[*] Connecting to MongoDB at {MONGODB_URL}...")
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("[OK] MongoDB connection successful")
        
        # Get server info
        server_info = client.server_info()
        print(f"[OK] MongoDB version: {server_info.get('version', 'unknown')}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
        print("\nPlease ensure:")
        print("  1. MongoDB is running")
        print("  2. MONGODB_URL is correct in your .env file")
        print("  3. You have necessary permissions")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("MONGODB VECTOR STORE TEST SUITE")
    print("=" * 70)
    
    # Test 0: Connection
    if not test_mongodb_connection():
        print("\n❌ Cannot proceed with tests - MongoDB connection failed")
        return False
    
    # Run tests
    try:
        # Test 1: Basic operations
        if not test_basic_operations():
            print("\n❌ Basic operations test failed")
            return False
        
        # Test 2: Retriever interface
        if not test_retriever_interface():
            print("\n❌ Retriever interface test failed")
            return False
        
        # Test 3: From texts
        if not test_from_texts():
            print("\n❌ From texts test failed")
            return False
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nMongoDB vector store is working correctly.")
        print("\nNext steps:")
        print("  1. Run migration: python migrate_vectorstore_to_mongodb.py")
        print("  2. Update .env: VECTORSTORE_BACKEND=mongodb")
        print("  3. Restart your application")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[*] Tests cancelled by user")
        sys.exit(0)

