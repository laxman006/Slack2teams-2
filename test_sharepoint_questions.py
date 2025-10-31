"""
Test SharePoint knowledge with real questions
"""
import requests
import json
import time

def test_chatbot(question):
    """Send a question to the chatbot and get response."""
    url = "http://localhost:8002/chat"
    
    payload = {
        "question": question,
        "session_id": "test_session_sharepoint"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            return data.get("answer", "No response")
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

def main():
    print("\n" + "="*80)
    print("🧪 TESTING SHAREPOINT KNOWLEDGE IN CHATBOT")
    print("="*80 + "\n")
    
    # SharePoint-specific questions
    test_questions = [
        "What are Multi User Golden Image Combinations?",
        "How do I migrate from Slack to Teams?",
        "What features are supported for Box to OneDrive migration?",
        "Tell me about message migration combinations",
        "What is the difference between Slack to Teams and Slack to Google Chat migration?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}: {question}")
        print(f"{'='*80}\n")
        
        print("⏳ Sending question to chatbot...")
        start_time = time.time()
        
        answer = test_chatbot(question)
        
        duration = time.time() - start_time
        
        print(f"✅ Response received in {duration:.2f}s\n")
        print("📝 Answer:")
        print("-" * 80)
        print(answer)
        print("-" * 80)
        
        # Check if response contains SharePoint-related content
        if any(keyword in answer.lower() for keyword in ['migration', 'sharepoint', 'slack', 'teams', 'box', 'onedrive', 'source']):
            print("\n✅ PASS: Response contains SharePoint knowledge!")
        else:
            print("\n⚠️  WARNING: Response may not contain SharePoint-specific information")
        
        # Wait between questions
        if i < len(test_questions):
            print("\n⏸️  Waiting 2 seconds before next question...\n")
            time.sleep(2)
    
    print("\n" + "="*80)
    print("🎉 TESTING COMPLETE!")
    print("="*80)

if __name__ == "__main__":
    main()

