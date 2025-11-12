"""
Retrieval Smoke Test
====================

Quick test to verify vectorstore and retrieval pipeline are working.
Tests basic retrieval, deduplication, and context size limits.
"""

import sys
from app.vectorstore import vectorstore
from app.llm import setup_qa_chain


def test_vectorstore_health():
    """Test if vectorstore is available and has documents."""
    print("="*70)
    print("VECTORSTORE HEALTH CHECK")
    print("="*70)
    
    try:
        # Test similarity search with a simple query
        test_query = "CloudFuze"
        results = vectorstore.similarity_search(test_query, k=5)
        
        print(f"\n✅ Vectorstore is accessible")
        print(f"📊 Retrieved {len(results)} documents for query: '{test_query}'")
        
        if results:
            print(f"\n📄 Sample document:")
            sample = results[0]
            print(f"   Source: {sample.metadata.get('source', 'unknown')}")
            print(f"   Tag: {sample.metadata.get('tag', 'unknown')}")
            print(f"   Content preview: {sample.page_content[:100]}...")
        else:
            print("\n⚠️  No documents found - vectorstore may be empty")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Vectorstore health check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieval_with_context():
    """Test retrieval with context size limiting."""
    print("\n" + "="*70)
    print("RETRIEVAL CONTEXT TEST")
    print("="*70)
    
    try:
        test_queries = [
            "how does JSON Slack migration work",
            "what is CloudFuze",
            "tell me about API access"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            print("-" * 70)
            
            # Perform retrieval
            docs = vectorstore.similarity_search(query, k=25)
            print(f"   Initial retrieval: {len(docs)} documents")
            
            # Simulate deduplication (simplified)
            import hashlib
            seen_ids = set()
            unique_docs = []
            
            for doc in docs:
                doc_key = (doc.metadata.get('source', '') + doc.page_content[:500])
                doc_id = hashlib.md5(doc_key.encode('utf-8')).hexdigest()
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    unique_docs.append(doc)
            
            print(f"   After deduplication: {len(unique_docs)} documents")
            
            # Apply context limit
            MAX_CONTEXT_DOCS = 10
            final_docs = unique_docs[:MAX_CONTEXT_DOCS]
            print(f"   After context limit: {len(final_docs)} documents")
            
            # Estimate context size
            total_chars = sum(len(doc.page_content) for doc in final_docs)
            estimated_tokens = total_chars // 4  # Rough estimate
            print(f"   Estimated tokens: ~{estimated_tokens}")
            
            if estimated_tokens > 8000:
                print(f"   ⚠️  Warning: Context may be too large")
            else:
                print(f"   ✅ Context size looks good")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Retrieval test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qa_chain_invoke():
    """Test the full QA chain invocation."""
    print("\n" + "="*70)
    print("QA CHAIN INVOCATION TEST")
    print("="*70)
    
    try:
        # Setup QA chain
        retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
        qa_chain = setup_qa_chain(retriever)
        
        print(f"\n✅ QA chain initialized successfully")
        
        # Test query
        test_query = "What is CloudFuze?"
        print(f"\n📝 Test Query: {test_query}")
        print("-" * 70)
        
        # Invoke chain
        result = qa_chain.invoke({
            "query": test_query,
            "user_id": "test-user"
        })
        
        answer = result.get("result", "")
        print(f"\n✅ Generated answer ({len(answer)} chars):")
        print(f"\n{answer[:300]}...")
        
        if len(answer) < 50:
            print(f"\n⚠️  Warning: Answer seems too short")
        elif "CloudFuze" not in answer and "cloudfuze" not in answer.lower():
            print(f"\n⚠️  Warning: Answer may not be relevant")
        else:
            print(f"\n✅ Answer looks reasonable")
        
        return True
        
    except Exception as e:
        print(f"\n❌ QA chain test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_deduplication_effectiveness():
    """Test deduplication with intentional duplicates."""
    print("\n" + "="*70)
    print("DEDUPLICATION TEST")
    print("="*70)
    
    try:
        # Run same query multiple times and collect docs
        query = "CloudFuze migration"
        all_docs = []
        
        for _ in range(3):
            docs = vectorstore.similarity_search(query, k=10)
            all_docs.extend(docs)
        
        print(f"\n📚 Collected {len(all_docs)} documents (with potential duplicates)")
        
        # Apply deduplication
        import hashlib
        seen_ids = set()
        unique_docs = []
        
        for doc in all_docs:
            doc_key = (doc.metadata.get('source', '') + doc.page_content[:500])
            doc_id = hashlib.md5(doc_key.encode('utf-8')).hexdigest()
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_docs.append(doc)
        
        dedup_rate = ((len(all_docs) - len(unique_docs)) / len(all_docs)) * 100
        print(f"✅ After deduplication: {len(unique_docs)} unique documents")
        print(f"📊 Removed {len(all_docs) - len(unique_docs)} duplicates ({dedup_rate:.1f}%)")
        
        if dedup_rate > 50:
            print(f"⚠️  High duplication rate - check retrieval strategy")
        else:
            print(f"✅ Deduplication working as expected")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Deduplication test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🧪 RUNNING RETRIEVAL SMOKE TESTS\n")
    
    results = {
        "vectorstore_health": False,
        "retrieval_context": False,
        "qa_chain": False,
        "deduplication": False
    }
    
    # Run tests
    results["vectorstore_health"] = test_vectorstore_health()
    
    if results["vectorstore_health"]:
        results["retrieval_context"] = test_retrieval_with_context()
        results["deduplication"] = test_deduplication_effectiveness()
        results["qa_chain"] = test_qa_chain_invoke()
    else:
        print("\n⚠️  Skipping remaining tests due to vectorstore failure")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} | {test_name.replace('_', ' ').title()}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All smoke tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed - check output above for details")
        sys.exit(1)

