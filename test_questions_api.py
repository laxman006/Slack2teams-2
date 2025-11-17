#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test questions via API and monitor backend responses
"""

import requests
import json
import time

BASE_URL = "http://localhost:8002"

# Test questions
questions = [
    "Does CloudFuze maintain 'created by' metadata when migrating SharePoint to OneDrive?",
    "How does JSON work in Slack to Teams migration?",
    "How does CloudFuze handle permission mapping when migrating shared folders from Google Drive to Microsoft 365 OneDrive?",
    "Does CloudFuze migrate Groups from Box to MS?",
    "How many messages can we migrate per day from slack to teams?",
    "What metadata is migrated from dropbox to google?"
]

print("=" * 80)
print("  TESTING CHATBOT WITH SHAREPOINT QUESTIONS")
print("=" * 80)

# Test health first
try:
    health = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"\n✓ Server health: {health.json()}")
except Exception as e:
    print(f"\n✗ Server not responding: {e}")
    exit(1)

print("\n" + "=" * 80)
print("  RUNNING TESTS")
print("=" * 80)

for i, question in enumerate(questions, 1):
    print(f"\n{'=' * 80}")
    print(f"Question {i}/{len(questions)}")
    print(f"{'=' * 80}")
    print(f"\n❓ {question}")
    
    try:
        # Make request (no auth needed if DISABLE_AUTH_FOR_TESTING=true)
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": question,
                "user_id": "test_user",
                "conversation_id": f"test_{i}"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "No response")
            metadata = data.get("metadata", {})
            
            print(f"\n✅ Response received:")
            print(f"\n{answer[:500]}...")
            if len(answer) > 500:
                print(f"\n(Full response: {len(answer)} characters)")
            
            # Show retrieval info
            if metadata:
                retrieval = metadata.get("retrieval", {})
                docs = retrieval.get("documents", {})
                print(f"\n📊 Retrieval Stats:")
                print(f"   Documents retrieved: {docs.get('retrieved', 0)}")
                print(f"   Documents used: {docs.get('used', 0)}")
                
        elif response.status_code == 401:
            print(f"\n❌ Authentication required")
            print(f"   Set DISABLE_AUTH_FOR_TESTING=true in .env")
            break
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"   {response.text[:200]}")
    
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
    
    # Wait between questions
    if i < len(questions):
        time.sleep(2)

print("\n" + "=" * 80)
print("  TEST COMPLETE")
print("=" * 80)
print("\nCheck backend logs for detailed retrieval information!")

