"""
Quick test of SharePoint knowledge - single question
"""
import requests
import time

print("\n" + "="*80)
print("🧪 QUICK SHAREPOINT TEST")
print("="*80 + "\n")

print("⏳ Waiting for server to be ready...")
time.sleep(3)

# Test a simple SharePoint question
question = "What are Multi User Golden Image Combinations?"

print(f"📝 Question: {question}\n")
print("⏳ Sending to chatbot...")

try:
    response = requests.post(
        'http://localhost:8002/chat',
        json={
            'question': question,
            'session_id': 'quick_test'
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        answer = data.get('answer', 'No answer')
        
        print("\n✅ RESPONSE RECEIVED!\n")
        print("="*80)
        print(answer)
        print("="*80 + "\n")
        
        # Check if SharePoint content is in the response
        if 'Multi User Golden Image' in answer or 'Box for Business' in answer or 'Dropbox for Business' in answer:
            print("✅ SUCCESS: Response contains SharePoint content!")
        elif "don't have specific information" in answer:
            print("⚠️  WARNING: Chatbot says it doesn't have the information")
        else:
            print("⚠️  UNCLEAR: Check if response is relevant")
            
    else:
        print(f"❌ Error: HTTP {response.status_code}")
        print(response.text)
        
except requests.exceptions.Timeout:
    print("❌ Request timed out - server may be processing too slowly")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80)


