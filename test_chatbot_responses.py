"""
Test chatbot responses with current vectorstore.

Tests various queries to verify the chatbot is returning correct,
relevant responses from the ingested data.
"""

import requests
import json
from datetime import datetime


# Server URL
BASE_URL = "http://localhost:8002"

# Test queries covering different topics
TEST_QUERIES = [
    # SharePoint/Migration related
    {
        "question": "How to migrate from Box to OneDrive?",
        "expected_keywords": ["box", "onedrive", "migration", "cloudfuze"],
        "category": "Migration"
    },
    {
        "question": "What are CloudFuze's security policies?",
        "expected_keywords": ["security", "policy", "compliance", "encryption"],
        "category": "Security"
    },
    {
        "question": "Tell me about SharePoint migration features",
        "expected_keywords": ["sharepoint", "migration", "features", "permissions"],
        "category": "Features"
    },
    {
        "question": "What file types does CloudFuze support?",
        "expected_keywords": ["file", "types", "support", "pdf", "docx"],
        "category": "Technical"
    },
    {
        "question": "How to handle large data migrations?",
        "expected_keywords": ["large", "data", "migration", "performance"],
        "category": "Migration"
    },
    # Blog related
    {
        "question": "What is zero downtime migration?",
        "expected_keywords": ["zero", "downtime", "migration", "enterprise"],
        "category": "Blog"
    },
    {
        "question": "How to migrate from Slack to Teams?",
        "expected_keywords": ["slack", "teams", "migration", "channels"],
        "category": "Migration"
    },
    # Pricing/Support
    {
        "question": "What are CloudFuze pricing plans?",
        "expected_keywords": ["pricing", "plan", "cost", "subscription"],
        "category": "Pricing"
    },
    {
        "question": "How do I contact CloudFuze support?",
        "expected_keywords": ["contact", "support", "email", "help"],
        "category": "Support"
    },
    # Technical
    {
        "question": "Does CloudFuze support PPTX files?",
        "expected_keywords": ["pptx", "powerpoint", "support", "file"],
        "category": "Technical"
    }
]


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_single_query(query_data):
    """Test a single query and evaluate the response."""
    question = query_data["question"]
    expected_keywords = query_data["expected_keywords"]
    category = query_data["category"]
    
    print(f"\n[{category}] Testing: \"{question}\"")
    print("-" * 80)
    
    try:
        # Make request to chatbot
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"question": question},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False
        
        data = response.json()
        answer = data.get("answer", "")
        
        # Check if we got an answer
        if not answer or len(answer) < 50:
            print(f"❌ FAILED: Answer too short or empty")
            print(f"   Answer: {answer}")
            return False
        
        # Check for expected keywords (case-insensitive)
        answer_lower = answer.lower()
        found_keywords = [kw for kw in expected_keywords if kw.lower() in answer_lower]
        missing_keywords = [kw for kw in expected_keywords if kw.lower() not in answer_lower]
        
        # Consider it a pass if at least 50% of keywords are found
        keyword_match_rate = len(found_keywords) / len(expected_keywords)
        
        if keyword_match_rate >= 0.5:
            print(f"✅ PASSED")
            print(f"   Keywords found: {len(found_keywords)}/{len(expected_keywords)} ({keyword_match_rate*100:.0f}%)")
            if found_keywords:
                print(f"   Matched: {', '.join(found_keywords)}")
            print(f"   Answer preview: {answer[:200]}...")
            return True
        else:
            print(f"⚠️  WEAK: Low keyword match")
            print(f"   Keywords found: {len(found_keywords)}/{len(expected_keywords)} ({keyword_match_rate*100:.0f}%)")
            if found_keywords:
                print(f"   Matched: {', '.join(found_keywords)}")
            if missing_keywords:
                print(f"   Missing: {', '.join(missing_keywords)}")
            print(f"   Answer preview: {answer[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Cannot connect to server at {BASE_URL}")
        print(f"   Make sure the server is running: python server.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all chatbot response tests."""
    print("\n" + "🤖" * 40)
    print("  CHATBOT RESPONSE TESTING")
    print("🤖" * 40)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Server: {BASE_URL}")
    print(f"Total queries: {len(TEST_QUERIES)}")
    
    # Check if server is running
    print("\n[*] Checking server connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print("[OK] Server is running and accessible")
    except:
        print(f"[ERROR] Cannot connect to server at {BASE_URL}")
        print("Please start the server first: python server.py")
        return 1
    
    # Run all tests
    print_section("RUNNING CHATBOT TESTS")
    
    results = []
    passed = 0
    failed = 0
    
    for query_data in TEST_QUERIES:
        result = test_single_query(query_data)
        results.append((query_data["question"], query_data["category"], result))
        if result:
            passed += 1
        else:
            failed += 1
    
    # Summary
    print_section("TEST SUMMARY")
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    print("\nDetailed Results:")
    for question, category, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} [{category}] {question}")
    
    # Category breakdown
    print("\nResults by Category:")
    categories = {}
    for question, category, result in results:
        if category not in categories:
            categories[category] = {"passed": 0, "total": 0}
        categories[category]["total"] += 1
        if result:
            categories[category]["passed"] += 1
    
    for category, stats in sorted(categories.items()):
        rate = (stats["passed"] / stats["total"] * 100)
        print(f"   {category}: {stats['passed']}/{stats['total']} ({rate:.0f}%)")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Chatbot is returning relevant responses from vectorstore")
        return 0
    elif passed >= len(results) * 0.7:  # 70% pass rate
        print("\n✅ MOST TESTS PASSED")
        print(f"\n{passed}/{len(results)} queries returned relevant responses")
        print("Review failed queries above for improvement opportunities")
        return 0
    else:
        print("\n⚠️  MANY TESTS FAILED")
        print("Check vectorstore data and retrieval configuration")
        return 1


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  CHATBOT RESPONSE TESTING")
    print("  This will test if the chatbot returns correct responses")
    print("  from the ingested SharePoint, Outlook, and blog data")
    print("=" * 80)
    
    print("\n[PREREQUISITE] Make sure:")
    print("  1. Server is running (python server.py)")
    print("  2. Vectorstore has been created (test_enhanced_ingestion.py)")
    print("  3. Data was ingested successfully\n")
    
    input("Press Enter to start testing...")
    
    exit(main())
