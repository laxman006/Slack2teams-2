#!/usr/bin/env python3
"""Test script to ask a question and see backend logs"""
import requests
import json
import os

# Check if auth is disabled
BASE_URL = "http://localhost:8002"
QUESTION = "Easily Manage Users in QuickBooks with CloudFuze Manage"

print("=" * 80)
print(f"Testing Question: {QUESTION}")
print("=" * 80)
print()

# Check if DISABLE_AUTH_FOR_TESTING is set
disable_auth = os.getenv("DISABLE_AUTH_FOR_TESTING", "false").lower() == "true"

if disable_auth:
    print("[INFO] Authentication is disabled for testing")
    headers = {}
else:
    print("[INFO] Authentication is required - checking for token...")
    # Try to get token from environment or use test token
    token = os.getenv("TEST_ACCESS_TOKEN")
    if token:
        headers = {"Authorization": f"Bearer {token}"}
    else:
        print("[WARNING] No token found. Set DISABLE_AUTH_FOR_TESTING=true in .env or provide TEST_ACCESS_TOKEN")
        headers = {}

print(f"\n[REQUEST] POST {BASE_URL}/chat")
print(f"[QUESTION] {QUESTION}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "question": QUESTION,
            "session_id": "test_session_123"
        },
        headers=headers,
        timeout=60
    )
    
    print(f"[STATUS] {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        answer = data.get("answer", "No answer")
        print(f"\n[RESPONSE]")
        print("-" * 80)
        print(answer)
        print("-" * 80)
        print(f"\n[TRACE_ID] {data.get('trace_id', 'N/A')}")
    elif response.status_code == 401:
        print("\n[ERROR] Authentication required")
        print("Set DISABLE_AUTH_FOR_TESTING=true in .env file")
    else:
        print(f"\n[ERROR] {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"\n[ERROR] Request failed: {e}")

print("\n" + "=" * 80)
print("Check backend server logs for detailed vectordb retrieval information!")
print("=" * 80)

