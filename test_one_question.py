"""
Test ONE SharePoint question with detailed output
"""
import requests
import json

question = "What features are supported for Box to OneDrive for Business migration?"

print(f"\n{'='*80}")
print(f"Testing: {question}")
print(f"{'='*80}\n")

try:
    print("⏳ Sending request...")
    response = requests.post(
        'http://localhost:8002/chat',
        json={'question': question, 'session_id': 'test123'},
        timeout=45
    )
    
    print(f"✅ Status: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        answer = data.get('answer', 'No answer')
        
        print("📝 ANSWER:")
        print("="*80)
        print(answer)
        print("="*80)
        
except Exception as e:
    print(f"❌ Error: {e}")

