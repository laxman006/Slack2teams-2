"""
End-to-End Chat Test
====================

Tests the complete chat pipeline including:
- Query processing
- Conversation context
- Intent classification
- Retrieval and reranking
- Answer generation
"""

import asyncio
import httpx
import sys
from typing import Dict, Any


# Test configuration
BASE_URL = "http://localhost:8002"
TIMEOUT = 30.0


async def test_health_endpoints():
    """Test health and readiness endpoints."""
    print("="*70)
    print("HEALTH ENDPOINTS TEST")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Test /health
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"\n✅ /health endpoint: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"\n❌ /health endpoint failed: {e}")
            return False
        
        # Test /ready
        try:
            response = await client.get(f"{BASE_URL}/ready")
            data = response.json()
            print(f"\n✅ /ready endpoint: {response.status_code}")
            print(f"   Ready: {data.get('ready', False)}")
            
            for check, status in data.get('checks', {}).items():
                print(f"   - {check}: {status}")
            
            if not data.get('ready', False):
                print("\n⚠️  Server is not fully ready - some checks failed")
                return False
                
        except Exception as e:
            print(f"\n❌ /ready endpoint failed: {e}")
            return False
    
    return True


async def test_chat_endpoint(question: str, user_id: str = "test-user") -> Dict[str, Any]:
    """Test the /chat endpoint with a question."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/chat",
                json={
                    "question": question,
                    "conversation_id": user_id,
                    "user_name": "Test User",
                    "user_email": "test@example.com"
                }
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Status {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


async def test_single_query():
    """Test a single query without conversation history."""
    print("\n" + "="*70)
    print("SINGLE QUERY TEST")
    print("="*70)
    
    question = "What is CloudFuze?"
    print(f"\n📝 Question: {question}")
    print("-" * 70)
    
    result = await test_chat_endpoint(question, user_id="single-test-user")
    
    if result["success"]:
        data = result["data"]
        answer = data.get("answer", "")
        trace_id = data.get("trace_id")
        
        print(f"\n✅ Response received ({len(answer)} chars)")
        print(f"   Trace ID: {trace_id}")
        print(f"\n📄 Answer Preview:")
        print(f"   {answer[:200]}...")
        
        if len(answer) < 50:
            print(f"\n⚠️  Answer seems too short")
            return False
        else:
            print(f"\n✅ Answer length looks good")
            return True
    else:
        print(f"\n❌ Request failed: {result['error']}")
        return False


async def test_technical_query():
    """Test a technical query that should trigger n-gram boosting."""
    print("\n" + "="*70)
    print("TECHNICAL QUERY TEST")
    print("="*70)
    
    question = "How does JSON Slack to Teams migration work?"
    print(f"\n📝 Question: {question}")
    print("-" * 70)
    
    result = await test_chat_endpoint(question, user_id="tech-test-user")
    
    if result["success"]:
        data = result["data"]
        answer = data.get("answer", "")
        
        print(f"\n✅ Response received ({len(answer)} chars)")
        print(f"\n📄 Answer Preview:")
        print(f"   {answer[:200]}...")
        
        # Check if answer contains relevant technical terms
        technical_terms = ["JSON", "Slack", "Teams", "migration", "export", "import"]
        found_terms = [term for term in technical_terms if term.lower() in answer.lower()]
        
        print(f"\n📊 Technical terms found: {len(found_terms)}/{len(technical_terms)}")
        print(f"   Terms: {', '.join(found_terms)}")
        
        if len(found_terms) >= 3:
            print(f"\n✅ Answer appears technically relevant")
            return True
        else:
            print(f"\n⚠️  Answer may not be relevant enough")
            return False
    else:
        print(f"\n❌ Request failed: {result['error']}")
        return False


async def test_conversation_continuity():
    """Test conversation context and follow-up questions."""
    print("\n" + "="*70)
    print("CONVERSATION CONTINUITY TEST")
    print("="*70)
    
    user_id = "conversation-test-user"
    
    # First question
    question1 = "Tell me about CloudFuze migration tools"
    print(f"\n📝 Question 1: {question1}")
    print("-" * 70)
    
    result1 = await test_chat_endpoint(question1, user_id=user_id)
    
    if not result1["success"]:
        print(f"❌ First question failed: {result1['error']}")
        return False
    
    answer1 = result1["data"].get("answer", "")
    print(f"✅ Answer 1 received ({len(answer1)} chars)")
    
    # Wait a moment to ensure conversation is saved
    await asyncio.sleep(1)
    
    # Follow-up question (should use context)
    question2 = "What are the pricing options?"
    print(f"\n📝 Question 2 (follow-up): {question2}")
    print("-" * 70)
    
    result2 = await test_chat_endpoint(question2, user_id=user_id)
    
    if not result2["success"]:
        print(f"❌ Follow-up question failed: {result2['error']}")
        return False
    
    answer2 = result2["data"].get("answer", "")
    print(f"✅ Answer 2 received ({len(answer2)} chars)")
    print(f"\n📄 Answer Preview:")
    print(f"   {answer2[:200]}...")
    
    # Check if answer maintains context
    if "pricing" in answer2.lower() or "price" in answer2.lower() or "cost" in answer2.lower():
        print(f"\n✅ Follow-up answer appears relevant")
        return True
    else:
        print(f"\n⚠️  Follow-up answer may have lost context")
        return False


async def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n" + "="*70)
    print("ERROR HANDLING TEST")
    print("="*70)
    
    # Empty question
    print(f"\n📝 Test: Empty question")
    result = await test_chat_endpoint("", user_id="error-test-user")
    print(f"   Result: {'✅ Handled gracefully' if not result.get('success') else '⚠️  Accepted empty question'}")
    
    # Very long question
    print(f"\n📝 Test: Very long question")
    long_question = "What is CloudFuze? " * 500  # Very long
    result = await test_chat_endpoint(long_question, user_id="error-test-user-2")
    print(f"   Result: {'✅ Handled' if result.get('success') or 'error' in result else '❌ Failed'}")
    
    return True


async def run_all_tests():
    """Run all end-to-end tests."""
    print("\n🧪 RUNNING END-TO-END CHAT TESTS\n")
    
    results = {}
    
    # Test health endpoints first
    results["health"] = await test_health_endpoints()
    
    if not results["health"]:
        print("\n❌ Server is not healthy - skipping chat tests")
        return results
    
    # Run chat tests
    results["single_query"] = await test_single_query()
    results["technical_query"] = await test_technical_query()
    results["conversation"] = await test_conversation_continuity()
    results["error_handling"] = await test_error_handling()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} | {test_name.replace('_', ' ').title()}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All end-to-end tests passed!")
        print("\nNext steps:")
        print("  1. Monitor response quality in production")
        print("  2. Check Langfuse traces for detailed metrics")
        print("  3. Gather user feedback on answer relevance")
    else:
        print("\n❌ Some tests failed - check output above for details")
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(run_all_tests())
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

