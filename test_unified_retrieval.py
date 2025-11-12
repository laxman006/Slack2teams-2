"""
Test Unified Retrieval Implementation
======================================

Tests the new unified retrieval pipeline with queries that previously failed
under the intent-based branching system.

Run this script after deploying unified retrieval to verify improvements.
"""

import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.vectorstore import vectorstore
from app.unified_retrieval import unified_retrieve
from app.ngram_retrieval import detect_technical_ngrams


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)


def test_query(query: str, description: str):
    """Test a single query and print detailed results."""
    print_section(f"TEST: {description}")
    print(f"Query: \"{query}\"\n")
    
    # Step 1: Detect N-grams
    detected_ngrams, ngram_weights = detect_technical_ngrams(query)
    print(f"[STEP 1] Detected N-grams: {detected_ngrams}")
    if ngram_weights:
        print(f"         Weights: {ngram_weights}")
    
    # Step 2: Retrieve documents
    try:
        doc_results = unified_retrieve(
            query=query,
            vectorstore=vectorstore,
            bm25_retriever=None,
            k=10  # Get top 10 for testing
        )
        
        print(f"\n[STEP 2] Retrieved {len(doc_results)} documents")
        
        # Step 3: Analyze top results
        if doc_results:
            print(f"\n[STEP 3] Top 5 Results:")
            for i, (doc, score) in enumerate(doc_results[:5], 1):
                metadata = doc.metadata
                source = metadata.get('source', 'Unknown')
                tag = metadata.get('tag', 'general')
                file_name = metadata.get('file_name', '')
                source_type = metadata.get('source_type', '')
                
                # Truncate content for display
                content_preview = doc.page_content[:150].replace('\n', ' ')
                
                print(f"\n   {i}. Score: {score:.4f}")
                print(f"      Source: {source}")
                print(f"      Tag: {tag}")
                if file_name:
                    print(f"      File: {file_name}")
                if source_type:
                    print(f"      Type: {source_type}")
                print(f"      Preview: {content_preview}...")
                
                # Check if detected keywords appear in document
                if detected_ngrams:
                    found_keywords = [kw for kw in detected_ngrams if kw in doc.page_content.lower()]
                    if found_keywords:
                        print(f"      ✅ Contains keywords: {found_keywords}")
        else:
            print("\n   ❌ No documents retrieved!")
        
        # Step 4: Success criteria
        print(f"\n[STEP 4] Success Criteria:")
        
        criteria_met = 0
        total_criteria = 4
        
        # Criterion 1: Retrieved documents
        if len(doc_results) > 0:
            print("   ✅ Documents retrieved")
            criteria_met += 1
        else:
            print("   ❌ No documents retrieved")
        
        # Criterion 2: Relevant keywords detected
        if detected_ngrams:
            print(f"   ✅ Keywords detected ({len(detected_ngrams)} terms)")
            criteria_met += 1
        else:
            print("   ❌ No keywords detected")
        
        # Criterion 3: Top document has good score
        if doc_results and doc_results[0][1] < 0.6:
            print(f"   ✅ Top document score is good ({doc_results[0][1]:.4f} < 0.6)")
            criteria_met += 1
        else:
            score_val = doc_results[0][1] if doc_results else 'N/A'
            print(f"   ⚠️  Top document score could be better ({score_val})")
        
        # Criterion 4: Detected keywords found in top results
        if detected_ngrams and doc_results:
            keyword_matches = sum(
                1 for doc, _ in doc_results[:5]
                if any(kw in doc.page_content.lower() for kw in detected_ngrams)
            )
            if keyword_matches >= 3:
                print(f"   ✅ Keywords found in top results ({keyword_matches}/5 docs)")
                criteria_met += 1
            else:
                print(f"   ⚠️  Keywords found in only {keyword_matches}/5 top docs")
        
        # Overall result
        success_rate = (criteria_met / total_criteria) * 100
        print(f"\n[RESULT] {criteria_met}/{total_criteria} criteria met ({success_rate:.0f}%)")
        
        if success_rate >= 75:
            print("   ✅ TEST PASSED")
        else:
            print("   ⚠️  TEST NEEDS IMPROVEMENT")
        
        return success_rate >= 75
        
    except Exception as e:
        print(f"\n   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all test queries."""
    print_section("UNIFIED RETRIEVAL TEST SUITE")
    print("Testing queries that previously failed with intent-based branching")
    
    # Check vectorstore
    try:
        doc_count = vectorstore._collection.count()
        print(f"\n✅ Vectorstore loaded: {doc_count} documents")
    except Exception as e:
        print(f"\n❌ Vectorstore error: {e}")
        return
    
    # Test queries (these failed before)
    test_cases = [
        {
            "query": "What is CloudFuze?",
            "description": "Basic Product Question",
            "expected": "Should retrieve blog posts and general product info"
        },
        {
            "query": "Does CloudFuze maintain created by metadata and permissions during SharePoint to OneDrive migration?",
            "description": "Metadata and Permissions Question",
            "expected": "Should detect 'metadata', 'permissions', 'sharepoint', 'onedrive'"
        },
        {
            "query": "How does JSON work in Slack to Teams migration?",
            "description": "Cross-Domain Technical Question",
            "expected": "Should detect 'json', 'slack', 'teams', 'migration'"
        },
        {
            "query": "Are migration logs available for OneDrive?",
            "description": "Logs and OneDrive Question",
            "expected": "Should retrieve OneDrive and logging documentation"
        },
        {
            "query": "What security certifications does CloudFuze have?",
            "description": "Security Compliance Question",
            "expected": "Should retrieve policy docs and certifications"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#'*80}")
        print(f"# TEST CASE {i}/{len(test_cases)}")
        print(f"{'#'*80}")
        print(f"Expected: {test_case['expected']}\n")
        
        success = test_query(test_case["query"], test_case["description"])
        results.append({
            "description": test_case["description"],
            "success": success
        })
    
    # Final summary
    print_section("FINAL SUMMARY")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"\nTests Passed: {passed}/{total} ({success_rate:.0f}%)\n")
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"  {i}. {result['description']}: {status}")
    
    print("\n" + "="*80)
    
    if success_rate >= 80:
        print("🎉 EXCELLENT! Unified retrieval is working great!")
    elif success_rate >= 60:
        print("✅ GOOD! Most tests passed. Minor improvements possible.")
    else:
        print("⚠️  NEEDS WORK. Check vectorstore content and N-gram configuration.")
    
    print("="*80)


if __name__ == "__main__":
    main()

