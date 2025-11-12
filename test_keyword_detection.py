"""
Keyword Detection Test
======================

Tests the improved unigram + N-gram detection.
Verifies that single technical words like "CloudFuze", "JSON", "metadata" are now detected.
"""

from app.ngram_retrieval import detect_technical_ngrams, is_technical_query

def test_unigram_detection():
    """Test that single technical words are now detected."""
    print("="*70)
    print("UNIGRAM DETECTION TEST")
    print("="*70)
    
    test_cases = [
        # (query, expected_keywords_to_find)
        ("what is cloudfuze", ["cloudfuze"]),
        ("how does json slack to teams migration work", ["json", "slack", "teams", "migration"]),
        ("does cloudfuze maintain created by metadata", ["cloudfuze", "created", "metadata"]),
        ("what are the permissions for sharepoint", ["permissions", "sharepoint"]),
        ("tell me about api authentication", ["api", "authentication"]),
        ("compliance and encryption features", ["compliance", "encryption"]),
    ]
    
    all_passed = True
    
    for query, expected in test_cases:
        print(f"\n📝 Query: {query}")
        print("-" * 70)
        
        detected, weights = detect_technical_ngrams(query)
        is_tech = is_technical_query(query)
        
        print(f"   Detected: {detected}")
        print(f"   Is Technical: {is_tech}")
        
        # Check if expected keywords were found
        found_all = all(keyword in detected for keyword in expected)
        
        if found_all:
            print(f"   ✅ PASS - All expected keywords detected: {expected}")
        else:
            missing = [k for k in expected if k not in detected]
            print(f"   ❌ FAIL - Missing keywords: {missing}")
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70 + "\n")
    
    return all_passed


def test_phrase_detection():
    """Test that multi-word phrases are still detected."""
    print("\n" + "="*70)
    print("PHRASE DETECTION TEST")
    print("="*70)
    
    test_cases = [
        ("slack to teams migration guide", ["slack to teams"]),
        ("api access token management", ["api access", "access token"]),
        ("metadata mapping for sharepoint", ["metadata mapping", "sharepoint"]),
    ]
    
    all_passed = True
    
    for query, expected_phrases in test_cases:
        print(f"\n📝 Query: {query}")
        print("-" * 70)
        
        detected, weights = detect_technical_ngrams(query)
        
        print(f"   Detected: {detected}")
        
        # Check if expected phrases were found
        found_all = all(phrase in detected for phrase in expected_phrases)
        
        if found_all:
            print(f"   ✅ PASS - All expected phrases detected")
        else:
            missing = [p for p in expected_phrases if p not in detected]
            print(f"   ❌ FAIL - Missing phrases: {missing}")
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL PHRASE TESTS PASSED")
    else:
        print("❌ SOME PHRASE TESTS FAILED")
    print("="*70 + "\n")
    
    return all_passed


def test_combined_detection():
    """Test that both unigrams and phrases are detected together."""
    print("\n" + "="*70)
    print("COMBINED DETECTION TEST")
    print("="*70)
    
    query = "how does json slack to teams migration work with metadata permissions"
    
    print(f"\n📝 Query: {query}")
    print("-" * 70)
    
    detected, weights = detect_technical_ngrams(query)
    is_tech = is_technical_query(query)
    
    print(f"   Detected keywords: {detected}")
    print(f"   Weights: {weights}")
    print(f"   Is Technical: {is_tech}")
    
    # Should detect both unigrams and phrases
    expected_unigrams = ["json", "migration", "metadata", "permissions"]
    expected_phrases = ["slack to teams"]
    
    unigrams_found = all(u in detected for u in expected_unigrams)
    phrases_found = all(p in detected for p in expected_phrases)
    
    if unigrams_found and phrases_found:
        print(f"\n   ✅ PASS - Both unigrams and phrases detected correctly")
        print(f"   Expected unigrams: {expected_unigrams} - {'✅ Found' if unigrams_found else '❌ Missing'}")
        print(f"   Expected phrases: {expected_phrases} - {'✅ Found' if phrases_found else '❌ Missing'}")
        return True
    else:
        print(f"\n   ❌ FAIL - Some keywords missing")
        missing_unigrams = [u for u in expected_unigrams if u not in detected]
        missing_phrases = [p for p in expected_phrases if p not in detected]
        if missing_unigrams:
            print(f"   Missing unigrams: {missing_unigrams}")
        if missing_phrases:
            print(f"   Missing phrases: {missing_phrases}")
        return False


def test_real_world_queries():
    """Test with the actual queries mentioned in the issue."""
    print("\n" + "="*70)
    print("REAL WORLD QUERIES TEST")
    print("="*70)
    
    queries = [
        "what is cloudfuze",
        "does cloudfuze maintain 'created by' metadata permissions for SharePoint to OneDrive migrations",
        "how does json slack to teams migration works",
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 70)
        
        detected, weights = detect_technical_ngrams(query)
        
        print(f"   Detected keywords: {detected}")
        print(f"   Count: {len(detected)}")
        
        if len(detected) > 0:
            print(f"   ✅ Keywords detected (was: [])")
        else:
            print(f"   ❌ Still no keywords detected")
    
    print("\n" + "="*70)
    print("Real world queries test complete")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\n🧪 TESTING IMPROVED KEYWORD DETECTION\n")
    
    try:
        # Run all tests
        test1 = test_unigram_detection()
        test2 = test_phrase_detection()
        test3 = test_combined_detection()
        test_real_world_queries()
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"  Unigram Detection: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"  Phrase Detection:  {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"  Combined Detection: {'✅ PASS' if test3 else '❌ FAIL'}")
        
        if test1 and test2 and test3:
            print("\n✅ All tests passed! Keyword detection is working correctly.")
            print("\nNext steps:")
            print("  1. Rebuild Docker: docker-compose down && docker-compose build")
            print("  2. Start server: docker-compose up -d")
            print("  3. Test queries in UI and watch logs for [N-GRAM DETECTION]")
        else:
            print("\n❌ Some tests failed - check output above")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

