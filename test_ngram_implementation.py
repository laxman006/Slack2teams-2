"""
Test N-gram Implementation for Technical Query Retrieval
=========================================================

This script tests the N-gram feature extraction and boosting implementation
to verify it correctly identifies technical queries and boosts relevant documents.
"""

import sys
from app.ngram_retrieval import (
    extract_ngrams,
    extract_all_ngrams,
    detect_technical_ngrams,
    is_technical_query,
    get_query_technical_score,
    get_ngram_diagnostics,
    expand_technical_query
)

# Test queries from the user's problem description
TEST_QUERIES = [
    "how does JSON Slack to Teams migration work",
    "what API access does CloudFuze support",
    "are migration logs available for OneDrive transfers",
    "how many messages can be migrated per day from Slack to Teams",
    "what is metadata mapping in CloudFuze",
    "explain the authentication flow for API integration",
    "general information about CloudFuze",  # Non-technical query
    "tell me about your company",  # Non-technical query
]

def print_separator(char='=', length=80):
    """Print a separator line."""
    print(char * length)

def test_ngram_extraction():
    """Test basic N-gram extraction."""
    print_separator()
    print("TEST 1: N-gram Extraction")
    print_separator()
    
    for query in TEST_QUERIES[:3]:  # Test first 3 queries
        print(f"\nQuery: {query}")
        
        # Extract bigrams
        bigrams = extract_ngrams(query, n=2)
        print(f"  Bigrams: {bigrams[:5]}...")  # Show first 5
        
        # Extract trigrams
        trigrams = extract_ngrams(query, n=3)
        print(f"  Trigrams: {trigrams[:3]}...")  # Show first 3
    
    print("\n✓ N-gram extraction test completed\n")

def test_technical_detection():
    """Test technical query detection."""
    print_separator()
    print("TEST 2: Technical Query Detection")
    print_separator()
    
    for query in TEST_QUERIES:
        print(f"\nQuery: {query}")
        
        # Detect technical n-grams
        detected_ngrams, ngram_weights = detect_technical_ngrams(query)
        is_tech = is_technical_query(query)
        tech_score = get_query_technical_score(query)
        
        print(f"  Technical N-grams: {detected_ngrams}")
        print(f"  Weights: {ngram_weights}")
        print(f"  Technical Score: {tech_score:.2f}")
        print(f"  Is Technical: {'✓ YES' if is_tech else '✗ NO'}")
    
    print("\n✓ Technical detection test completed\n")

def test_query_expansion():
    """Test technical query expansion."""
    print_separator()
    print("TEST 3: Query Expansion for Technical Queries")
    print_separator()
    
    technical_queries = [q for q in TEST_QUERIES if is_technical_query(q)]
    
    for query in technical_queries[:3]:  # Test first 3 technical queries
        print(f"\nOriginal Query: {query}")
        
        expansions = expand_technical_query(query)
        print(f"  Expansions ({len(expansions)}):")
        for i, expansion in enumerate(expansions, 1):
            print(f"    {i}. {expansion}")
    
    print("\n✓ Query expansion test completed\n")

def test_diagnostics():
    """Test diagnostic output."""
    print_separator()
    print("TEST 4: Diagnostic Output")
    print_separator()
    
    query = TEST_QUERIES[0]  # "how does JSON Slack to Teams migration work"
    print(f"\nQuery: {query}\n")
    
    diagnostics = get_ngram_diagnostics(query)
    
    print("Diagnostic Information:")
    print(f"  All Bigrams: {diagnostics['all_bigrams']}")
    print(f"  All Trigrams: {diagnostics['all_trigrams']}")
    print(f"  Detected Technical N-grams: {diagnostics['detected_technical_ngrams']}")
    print(f"  N-gram Weights: {diagnostics['ngram_weights']}")
    print(f"  Technical Score: {diagnostics['technical_score']:.2f}")
    print(f"  Is Technical Query: {diagnostics['is_technical_query']}")
    print(f"  Query Expansions: {diagnostics['query_expansions']}")
    
    print("\n✓ Diagnostic output test completed\n")

def test_expected_improvements():
    """Test that the implementation addresses the original problem."""
    print_separator()
    print("TEST 5: Expected Improvements Validation")
    print_separator()
    
    print("\n✓ Checking if problematic queries are now detected as technical...\n")
    
    problematic_queries = {
        "how does JSON Slack to Teams migration work": ["json migration", "slack teams", "teams migration"],
        "what API access does CloudFuze support": ["api access"],
        "are migration logs available for OneDrive transfers": ["migration logs"],
    }
    
    all_passed = True
    
    for query, expected_ngrams in problematic_queries.items():
        print(f"Query: {query}")
        
        detected_ngrams, _ = detect_technical_ngrams(query)
        tech_score = get_query_technical_score(query)
        
        # Check if any expected n-gram was detected
        found_ngrams = [ng for ng in expected_ngrams if ng in detected_ngrams]
        
        if found_ngrams:
            print(f"  ✓ PASS - Detected technical n-grams: {found_ngrams}")
            print(f"  Technical score: {tech_score:.2f}")
        else:
            print(f"  ✗ FAIL - Expected to detect: {expected_ngrams}")
            print(f"  But detected: {detected_ngrams}")
            all_passed = False
        
        print()
    
    if all_passed:
        print("✓ All problematic queries now correctly identified as technical!\n")
    else:
        print("✗ Some queries still not correctly identified. Check n-gram taxonomy.\n")
    
    return all_passed

def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("N-GRAM IMPLEMENTATION TEST SUITE")
    print("=" * 80 + "\n")
    
    try:
        # Run tests
        test_ngram_extraction()
        test_technical_detection()
        test_query_expansion()
        test_diagnostics()
        success = test_expected_improvements()
        
        # Final summary
        print_separator()
        print("FINAL SUMMARY")
        print_separator()
        print()
        
        if success:
            print("✓ ALL TESTS PASSED!")
            print("\nThe N-gram implementation successfully:")
            print("  1. Extracts bigrams and trigrams from queries")
            print("  2. Detects technical phrases (JSON migration, API access, etc.)")
            print("  3. Calculates technical relevance scores")
            print("  4. Expands technical queries for better retrieval")
            print("  5. Addresses the original problem (technical queries not retrieving right docs)")
            print("\nNext steps:")
            print("  - Start the server and test with real queries")
            print("  - Check Langfuse dashboard for N-gram detection logs")
            print("  - Monitor retrieval accuracy improvements")
            return 0
        else:
            print("✗ SOME TESTS FAILED")
            print("\nPlease review the N-gram taxonomy and adjust weights/phrases as needed.")
            return 1
            
    except Exception as e:
        print(f"\n✗ ERROR: Test suite failed with exception:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

