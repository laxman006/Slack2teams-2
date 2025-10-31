"""
Debug the API response to see what's being returned
"""
import requests
import json

url = "http://localhost:8002/chat"

payload = {
    "message": "What are Multi User Golden Image Combinations?",
    "session_id": "debug_test"
}

print("Sending request to:", url)
print("Payload:", json.dumps(payload, indent=2))
print("\n" + "="*80)

try:
    response = requests.post(url, json=payload, timeout=60)
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print("\nFull Response:")
    print("="*80)
    
    # Try to parse as JSON
    try:
        json_response = response.json()
        print(json.dumps(json_response, indent=2))
    except:
        # If not JSON, print raw text
        print(response.text)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

