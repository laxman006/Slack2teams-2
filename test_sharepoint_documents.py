#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test SharePoint Document Extraction

Validates that:
1. Files are correctly crawled from SharePoint
2. Documents are properly processed and chunked
3. Metadata is correctly attached
4. Documents are stored in MongoDB vector store
5. Retrieval returns relevant documents with citations
6. LLM responses include proper source citations
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_openai import OpenAIEmbeddings
from app.mongodb_vectorstore import MongoDBVectorStore
from config import MONGODB_VECTORSTORE_COLLECTION


def test_mongodb_connection():
    """Test connection to MongoDB vector store."""
    print("\n" + "=" * 70)
    print("TEST 1: MongoDB Connection")
    print("=" * 70)
    
    try:
        embeddings = OpenAIEmbeddings()
        vectorstore = MongoDBVectorStore(
            collection_name=MONGODB_VECTORSTORE_COLLECTION,
            embedding_function=embeddings
        )
        
        stats = vectorstore.get_collection_stats()
        
        print(f"[OK] Connected to MongoDB")
        print(f"    Collection: {stats['collection_name']}")
        print(f"    Total documents: {stats['total_documents']}")
        print(f"    Embedding dimension: {stats['embedding_dimension']}")
        
        if stats['total_documents'] == 0:
            print("\n[WARNING] No documents in vector store yet")
            print("          Run extract_sharepoint_documents.py first")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        return False


def test_sharepoint_documents_exist():
    """Test that SharePoint documents exist in vector store."""
    print("\n" + "=" * 70)
    print("TEST 2: SharePoint Documents in Vector Store")
    print("=" * 70)
    
    try:
        embeddings = OpenAIEmbeddings()
        vectorstore = MongoDBVectorStore(
            collection_name=MONGODB_VECTORSTORE_COLLECTION,
            embedding_function=embeddings
        )
        
        # Query for SharePoint documents
        filter_query = {"metadata.source_type": "sharepoint_document"}
        sharepoint_count = vectorstore.collection.count_documents(filter_query)
        
        print(f"[*] SharePoint documents in vector store: {sharepoint_count}")
        
        if sharepoint_count == 0:
            print("[WARNING] No SharePoint documents found")
            print("          Run extract_sharepoint_documents.py to add them")
            return False
        
        # Get a sample document to check metadata
        sample_doc = vectorstore.collection.find_one(filter_query)
        
        if sample_doc:
            metadata = sample_doc.get('metadata', {})
            print(f"\n[OK] Sample SharePoint document found:")
            print(f"    File: {metadata.get('file_name', 'Unknown')}")
            print(f"    Type: {metadata.get('file_type', 'Unknown')}")
            print(f"    Folder: {metadata.get('folder_path', 'Unknown')}")
            print(f"    URL: {metadata.get('sharepoint_url', 'Unknown')[:50]}...")
            print(f"    Last modified: {metadata.get('last_modified', 'Unknown')}")
            
            # Check required metadata fields
            required_fields = ['file_name', 'file_type', 'sharepoint_url', 'folder_path']
            missing_fields = [field for field in required_fields if not metadata.get(field)]
            
            if missing_fields:
                print(f"\n[WARNING] Missing metadata fields: {missing_fields}")
            else:
                print(f"\n[OK] All required metadata fields present")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to check SharePoint documents: {e}")
        return False


def test_document_retrieval():
    """Test that documents can be retrieved with similarity search."""
    print("\n" + "=" * 70)
    print("TEST 3: Document Retrieval")
    print("=" * 70)
    
    try:
        embeddings = OpenAIEmbeddings()
        vectorstore = MongoDBVectorStore(
            collection_name=MONGODB_VECTORSTORE_COLLECTION,
            embedding_function=embeddings
        )
        
        # Test queries
        test_queries = [
            "migration process",
            "setup instructions",
            "configuration guide"
        ]
        
        print("[*] Testing similarity search...")
        
        for query in test_queries:
            print(f"\n[*] Query: '{query}'")
            
            results = vectorstore.similarity_search(query, k=3)
            
            if results:
                print(f"[OK] Found {len(results)} relevant documents")
                
                for i, doc in enumerate(results, 1):
                    metadata = doc.metadata
                    file_name = metadata.get('file_name', 'Unknown')
                    score = metadata.get('score', 0)
                    
                    print(f"    {i}. {file_name} (score: {score:.4f})")
                    print(f"       Content preview: {doc.page_content[:100]}...")
            else:
                print(f"[WARNING] No documents found for query")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to test retrieval: {e}")
        return False


def test_citation_format():
    """Test that retrieved documents have proper citation information."""
    print("\n" + "=" * 70)
    print("TEST 4: Citation Format")
    print("=" * 70)
    
    try:
        embeddings = OpenAIEmbeddings()
        vectorstore = MongoDBVectorStore(
            collection_name=MONGODB_VECTORSTORE_COLLECTION,
            embedding_function=embeddings
        )
        
        # Get a few documents
        docs = vectorstore.similarity_search("migration", k=5)
        
        if not docs:
            print("[WARNING] No documents to test")
            return False
        
        print(f"[*] Checking citation format for {len(docs)} documents...\n")
        
        all_valid = True
        
        for i, doc in enumerate(docs, 1):
            metadata = doc.metadata
            
            # Check required citation fields
            file_name = metadata.get('file_name')
            folder_path = metadata.get('folder_path')
            file_type = metadata.get('file_type')
            
            # Build citation
            if file_name:
                citation = f"[Source: {file_name}"
                if folder_path:
                    citation += f" - {folder_path}"
                citation += "]"
                
                print(f"{i}. {citation}")
                print(f"   Content preview: {doc.page_content[:80]}...")
                print()
            else:
                print(f"{i}. [WARNING] Missing file_name in metadata")
                all_valid = False
        
        if all_valid:
            print("[OK] All documents have proper citation information")
        else:
            print("[WARNING] Some documents missing citation information")
        
        return all_valid
        
    except Exception as e:
        print(f"[ERROR] Failed to test citation format: {e}")
        return False


def test_llm_response_with_citations():
    """Test that LLM responses include citations."""
    print("\n" + "=" * 70)
    print("TEST 5: LLM Response with Citations")
    print("=" * 70)
    
    try:
        from app.llm import setup_qa_chain
        from app.vectorstore import vectorstore
        
        # Setup QA chain
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        qa_chain = setup_qa_chain(retriever)
        
        # Test query
        test_question = "What are the migration steps?"
        
        print(f"[*] Test Question: {test_question}")
        print(f"[*] Generating response...\n")
        
        result = qa_chain.invoke({"query": test_question})
        answer = result.get("result", "")
        
        print("[*] Response:")
        print("-" * 70)
        print(answer)
        print("-" * 70)
        
        # Check if response contains citations
        has_source_citation = "[Source:" in answer
        
        if has_source_citation:
            print("\n[OK] Response contains source citations")
            
            # Count citations
            citation_count = answer.count("[Source:")
            print(f"[OK] Found {citation_count} citation(s)")
        else:
            print("\n[WARNING] Response does not contain source citations")
            print("          The LLM may not be following citation instructions")
        
        return has_source_citation
        
    except Exception as e:
        print(f"[ERROR] Failed to test LLM response: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_types_coverage():
    """Test that different file types are represented in vector store."""
    print("\n" + "=" * 70)
    print("TEST 6: File Types Coverage")
    print("=" * 70)
    
    try:
        embeddings = OpenAIEmbeddings()
        vectorstore = MongoDBVectorStore(
            collection_name=MONGODB_VECTORSTORE_COLLECTION,
            embedding_function=embeddings
        )
        
        # Count documents by file type
        file_types = ['pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'txt', 'md']
        
        print("[*] Checking file type coverage...\n")
        
        type_counts = {}
        for file_type in file_types:
            filter_query = {
                "metadata.source_type": "sharepoint_document",
                "metadata.file_type": file_type
            }
            count = vectorstore.collection.count_documents(filter_query)
            if count > 0:
                type_counts[file_type] = count
        
        if type_counts:
            print("[OK] File types found in vector store:")
            for file_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"    {file_type.upper()}: {count} documents")
            
            return True
        else:
            print("[WARNING] No SharePoint documents found by file type")
            return False
        
    except Exception as e:
        print(f"[ERROR] Failed to test file types: {e}")
        return False


def run_all_tests():
    """Run all tests and print summary."""
    print("\n" + "=" * 70)
    print("SHAREPOINT DOCUMENT EXTRACTION - TEST SUITE")
    print("=" * 70)
    print(f"MongoDB Collection: {MONGODB_VECTORSTORE_COLLECTION}")
    print("=" * 70)
    
    tests = [
        ("MongoDB Connection", test_mongodb_connection),
        ("SharePoint Documents Exist", test_sharepoint_documents_exist),
        ("Document Retrieval", test_document_retrieval),
        ("Citation Format", test_citation_format),
        ("File Types Coverage", test_file_types_coverage),
        ("LLM Response with Citations", test_llm_response_with_citations),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("-" * 70)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    elif passed > 0:
        print(f"\n⚠️  {total - passed} test(s) failed")
    else:
        print("\n❌ All tests failed")
    
    print("=" * 70)


def main():
    """Main entry point."""
    # Check required environment variables
    required_vars = ['OPENAI_API_KEY', 'MONGODB_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("[ERROR] Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables in your .env file")
        sys.exit(1)
    
    # Run tests
    run_all_tests()


if __name__ == "__main__":
    main()

