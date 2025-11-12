#!/usr/bin/env python3
"""
Test Query Context Relevance Checker

This script tests if specific queries retrieve relevant context from the vector store.
It checks:
1. If documents are retrieved
2. What type of documents are retrieved (blog, sharepoint, etc.)
3. The relevance of retrieved documents
4. Source information for each document

Usage:
    python test_query_context_relevance.py
"""

import os
import sys
from datetime import datetime

# Set environment variables BEFORE importing app modules
os.environ["INITIALIZE_VECTORSTORE"] = "false"  # Don't rebuild, just query

from dotenv import load_dotenv
load_dotenv()

from app.vectorstore import vectorstore
from app.endpoints import hybrid_retrieve, detect_intent, expand_query_with_intent

def analyze_query_context(query: str):
    """
    Analyze what context would be retrieved for a given query.
    
    Args:
        query: User question to test
    
    Returns:
        dict: Analysis results
    """
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)
    
    if vectorstore is None:
        print("❌ ERROR: Vectorstore not initialized!")
        return {
            "query": query,
            "error": "Vectorstore not initialized",
            "has_context": False
        }
    
    try:
        # 1. Detect intent
        intent, confidence, method = detect_intent(query, None)
        print(f"\n[INTENT DETECTION]")
        print(f"  Intent: {intent}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Method: {method}")
        
        # 2. Expand query
        expanded_query = expand_query_with_intent(query, intent)
        print(f"\n[QUERY EXPANSION]")
        print(f"  Original: {query}")
        print(f"  Expanded: {expanded_query}")
        
        # 3. Hybrid retrieval
        print(f"\n[HYBRID RETRIEVAL]")
        doc_results = hybrid_retrieve(expanded_query, k=25)
        
        print(f"  Retrieved {len(doc_results)} documents")
        
        if len(doc_results) == 0:
            print("\n❌ NO CONTEXT FOUND - Query would not retrieve any relevant documents")
            return {
                "query": query,
                "intent": intent,
                "confidence": confidence,
                "has_context": False,
                "document_count": 0
            }
        
        # 4. Analyze retrieved documents
        print(f"\n[DOCUMENT ANALYSIS]")
        
        sources = {}
        source_types = {}
        
        for i, result in enumerate(doc_results[:10], 1):  # Show top 10
            # Handle both tuple formats: (doc, score) or (doc, score, metadata)
            if isinstance(result, tuple):
                doc = result[0]
                score = result[1] if len(result) > 1 else "N/A"
            else:
                doc = result
                score = "N/A"
            
            metadata = doc.metadata
            source = metadata.get('source', 'Unknown')
            source_type = metadata.get('source_type', 'Unknown')
            
            # Count sources
            sources[source] = sources.get(source, 0) + 1
            source_types[source_type] = source_types.get(source_type, 0) + 1
            
            print(f"\n  Document #{i}:")
            print(f"    Score: {score}")
            print(f"    Source Type: {source_type}")
            print(f"    Source: {source}")
            
            # Show content preview
            content_preview = doc.page_content[:200].replace('\n', ' ')
            print(f"    Content: {content_preview}...")
        
        # 5. Summary
        print(f"\n[SUMMARY]")
        print(f"  Total Documents: {len(doc_results)}")
        print(f"  Source Types:")
        for stype, count in source_types.items():
            print(f"    - {stype}: {count} documents")
        
        print(f"\n  Top Sources:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {source}: {count} documents")
        
        # 6. Relevance assessment
        has_relevant_context = len(doc_results) > 0
        
        # Check if documents are from relevant sources
        relevant_sources = ['blog', 'sharepoint', 'pdf', 'excel', 'doc']
        has_known_sources = any(stype.lower() in relevant_sources for stype in source_types.keys())
        
        print(f"\n[RELEVANCE ASSESSMENT]")
        if has_relevant_context and has_known_sources:
            print(f"  ✅ CONTEXT FOUND: Query retrieves relevant documents from known sources")
        elif has_relevant_context:
            print(f"  ⚠️  CONTEXT FOUND: Query retrieves documents but from unknown sources")
        else:
            print(f"  ❌ NO CONTEXT: Query does not retrieve relevant documents")
        
        return {
            "query": query,
            "intent": intent,
            "confidence": confidence,
            "has_context": has_relevant_context,
            "document_count": len(doc_results),
            "source_types": source_types,
            "top_sources": dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5])
        }
        
    except Exception as e:
        print(f"\n❌ ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
        return {
            "query": query,
            "error": str(e),
            "has_context": False
        }


def main():
    """Main function to test queries."""
    print("=" * 80)
    print("QUERY CONTEXT RELEVANCE CHECKER")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check if vectorstore is available
    if vectorstore is None:
        print("\n❌ ERROR: Vectorstore not initialized!")
        print("Please ensure the vectorstore is built before running this test.")
        print("Run: python manage_vectorstore.py rebuild")
        sys.exit(1)
    
    print(f"\n✅ Vectorstore loaded successfully")
    doc_count = vectorstore._collection.count()
    print(f"Total documents in vectorstore: {doc_count}")
    
    # Test queries
    test_queries = [
        "does cloudfuze maintain 'create by' metadata when migrating sharepoint to one drive",
        "how does json slack to teams migration works",
        "What API access does CloudFuze support",
        "Are migration logs available for OneDrive transfers"
    ]
    
    print("\n" + "=" * 80)
    print("TESTING QUERIES")
    print("=" * 80)
    
    results = []
    
    for query in test_queries:
        result = analyze_query_context(query)
        results.append(result)
    
    # Final summary
    print("\n\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        query = result['query']
        has_context = result.get('has_context', False)
        doc_count = result.get('document_count', 0)
        
        print(f"\n{i}. {query}")
        
        if 'error' in result:
            print(f"   ❌ ERROR: {result['error']}")
        elif has_context:
            print(f"   ✅ CONTEXT FOUND: {doc_count} documents retrieved")
            if 'source_types' in result:
                source_types = ', '.join([f"{k} ({v})" for k, v in result['source_types'].items()])
                print(f"   Sources: {source_types}")
        else:
            print(f"   ❌ NO CONTEXT: No relevant documents found in database")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

