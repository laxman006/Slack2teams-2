"""
N-gram Diagnostics Test Script
================================

Tests the n-gram detection and scoring functionality.
Run this to verify n-gram extraction and document ranking improvements.
"""

from app.ngram_retrieval import (
    detect_technical_ngrams,
    get_ngram_diagnostics,
    is_technical_query,
    rerank_documents_with_ngrams
)
from typing import List


def test_ngram_detection():
    """Test n-gram detection on various queries."""
    print("="*70)
    print("N-GRAM DETECTION TEST")
    print("="*70)
    
    test_queries = [
        "how does JSON Slack to Teams migration work",
        "what API access does CloudFuze support",
        "are migration logs available for OneDrive transfers",
        "tell me about metadata mapping in SharePoint",
        "what is the rate limiting for API endpoints",
        "general information about CloudFuze",  # Non-technical query
        "how do I get started",  # Non-technical query
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 70)
        
        # Get diagnostics
        diagnostics = get_ngram_diagnostics(query)
        
        # Print results
        detected = diagnostics['detected_technical_ngrams']
        weights = diagnostics['ngram_weights']
        score = diagnostics['technical_score']
        is_tech = diagnostics['is_technical_query']
        
        if detected:
            print(f"✅ Technical N-grams: {detected}")
            print(f"   Weights: {weights}")
            print(f"   Technical Score: {score:.2f}")
            print(f"   Is Technical: {is_tech}")
        else:
            print(f"❌ No technical n-grams detected")
            print(f"   Is Technical: {is_tech}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")


def test_ngram_scoring():
    """Test n-gram scoring on mock documents."""
    print("\n" + "="*70)
    print("N-GRAM SCORING TEST")
    print("="*70)
    
    query = "how does JSON Slack to Teams migration work"
    
    # Create mock documents
    class MockDocument:
        def __init__(self, content, metadata):
            self.page_content = content
            self.metadata = metadata
    
    mock_docs = [
        MockDocument(
            "This document discusses JSON migration from Slack to Teams workspace.",
            {"source": "doc1.pdf", "tag": "technical", "doc_type": "technical_doc"}
        ),
        MockDocument(
            "General information about CloudFuze platform and services.",
            {"source": "doc2.pdf", "tag": "general", "doc_type": "overview"}
        ),
        MockDocument(
            "API migration guide for Slack channels to Microsoft Teams.",
            {"source": "doc3.pdf", "tag": "api", "doc_type": "api_documentation"}
        ),
        MockDocument(
            "Metadata mapping and schema validation for migration projects.",
            {"source": "doc4.pdf", "tag": "technical", "doc_type": "implementation_guide"}
        ),
    ]
    
    print(f"\n📝 Query: {query}")
    print(f"📚 Documents: {len(mock_docs)}")
    print("-" * 70)
    
    # Rerank documents
    reranked = rerank_documents_with_ngrams(mock_docs, query)
    
    print("\n🏆 Reranked Results:")
    for i, (doc, score) in enumerate(reranked, 1):
        source = doc.metadata.get('source', 'unknown')
        tag = doc.metadata.get('tag', 'unknown')
        snippet = doc.page_content[:60] + "..."
        print(f"\n  #{i} | Score: {score:.4f}")
        print(f"      Source: {source} | Tag: {tag}")
        print(f"      Content: {snippet}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")


def test_weighted_combination():
    """Test the new weighted combination formula."""
    print("\n" + "="*70)
    print("WEIGHTED COMBINATION TEST")
    print("="*70)
    
    # Test different score combinations
    test_cases = [
        (0.9, 4.5),  # High semantic, high n-gram
        (0.9, 0.5),  # High semantic, low n-gram
        (0.3, 4.5),  # Low semantic, high n-gram
        (0.5, 2.0),  # Medium both
    ]
    
    print("\nTesting score combination formula:")
    print("Formula: 0.7 * semantic + 0.3 * (ngram_capped / 5.0)")
    print("-" * 70)
    
    for semantic_score, ngram_score in test_cases:
        ngram_capped = min(ngram_score, 5.0)
        ngram_norm = ngram_capped / 5.0
        combined = (0.7 * semantic_score) + (0.3 * ngram_norm)
        
        print(f"\n  Semantic: {semantic_score:.2f} | N-gram: {ngram_score:.2f}")
        print(f"  → Capped: {ngram_capped:.2f} | Normalized: {ngram_norm:.2f}")
        print(f"  → Combined: {combined:.4f}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\n" + "🧪 RUNNING N-GRAM DIAGNOSTICS TESTS" + "\n")
    
    try:
        # Run all tests
        test_ngram_detection()
        test_ngram_scoring()
        test_weighted_combination()
        
        print("\n✅ All tests completed successfully!")
        print("\nNext steps:")
        print("  1. Verify technical queries are detected correctly")
        print("  2. Check that scores are in reasonable ranges")
        print("  3. Confirm documents with matching n-grams rank higher")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

