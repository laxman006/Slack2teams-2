"""
Test questions and verify answers are coming from vector database
This script:
1. Shows what documents are retrieved from the vector store
2. Sends questions to the chatbot API
3. Compares retrieved content with the answer to verify vector retrieval
"""
import requests
import json
from langchain_openai import OpenAIEmbeddings
from app.mongodb_vectorstore import MongoDBVectorStore
from config import MONGODB_VECTORSTORE_COLLECTION
from dotenv import load_dotenv
import os
import time

load_dotenv()

# Test questions
TEST_QUESTIONS = [
    "What features are supported for Box to OneDrive for Business migration?",
    "How does Slack to Teams migration work?",
    "What are Multi User Golden Image Combinations?",
    "What is the purpose of CloudFuze?",
]

def get_vector_retrieval(query, k=5):
    """Retrieve documents from vector store for a query."""
    print(f"\n{'='*80}")
    print(f"🔍 VECTOR RETRIEVAL TEST")
    print(f"{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}\n")
    
    try:
        # Initialize embeddings and vectorstore
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        vectorstore = MongoDBVectorStore(
            collection_name=MONGODB_VECTORSTORE_COLLECTION,
            embedding_function=embeddings
        )
        
        # Retrieve documents
        print(f"📚 Retrieving top {k} documents from vector store...")
        results = vectorstore.similarity_search(query, k=k)
        
        print(f"✅ Retrieved {len(results)} documents\n")
        
        retrieved_docs = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get('source', 'Unknown')
            source_type = doc.metadata.get('source_type', 'Unknown')
            page_title = doc.metadata.get('page_title', 'N/A')
            page_url = doc.metadata.get('page_url', 'N/A')
            
            doc_info = {
                'rank': i,
                'source': source,
                'source_type': source_type,
                'page_title': page_title,
                'page_url': page_url,
                'content': doc.page_content,
                'content_preview': doc.page_content[:200]
            }
            retrieved_docs.append(doc_info)
            
            print(f"📄 Document {i}:")
            print(f"   Source: {source}")
            print(f"   Type: {source_type}")
            if page_title != 'N/A':
                print(f"   Title: {page_title}")
            if page_url != 'N/A':
                print(f"   URL: {page_url}")
            print(f"   Content Preview: {doc.page_content[:150]}...")
            print()
        
        return retrieved_docs
        
    except Exception as e:
        print(f"❌ Error retrieving from vector store: {e}")
        return []

def get_chatbot_answer(question, session_id='test_vector_session'):
    """Get answer from chatbot API."""
    print(f"\n{'='*80}")
    print(f"🤖 CHATBOT API TEST")
    print(f"{'='*80}")
    print(f"Question: {question}")
    print(f"{'='*80}\n")
    
    try:
        print("⏳ Sending request to chatbot API...")
        response = requests.post(
            'http://localhost:8002/chat',
            json={'question': question, 'session_id': session_id},
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', 'No answer')
            
            print(f"✅ Status: {response.status_code}\n")
            print("📝 CHATBOT ANSWER:")
            print("-" * 80)
            print(answer)
            print("-" * 80)
            
            return answer
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error calling chatbot API: {e}")
        return None

def verify_vector_usage(retrieved_docs, answer):
    """Verify if the answer uses content from retrieved documents."""
    print(f"\n{'='*80}")
    print(f"✅ VERIFICATION: Is answer from vector store?")
    print(f"{'='*80}\n")
    
    if not answer or not retrieved_docs:
        print("❌ Cannot verify - missing answer or retrieved docs")
        return False
    
    # Check for common keywords/phrases between retrieved docs and answer
    answer_lower = answer.lower()
    matches_found = 0
    
    for doc in retrieved_docs:
        content_lower = doc['content'].lower()
        
        # Find common significant words (5+ characters)
        content_words = set([w for w in content_lower.split() if len(w) > 5])
        answer_words = set([w for w in answer_lower.split() if len(w) > 5])
        
        common_words = content_words.intersection(answer_words)
        
        if len(common_words) > 3:  # If more than 3 significant words match
            matches_found += 1
            print(f"✅ Match found with Document {doc['rank']} (Source: {doc['source']})")
            print(f"   Common keywords: {', '.join(list(common_words)[:10])}")
            print(f"   Source type: {doc['source_type']}")
            if doc['page_title'] != 'N/A':
                print(f"   Page title: {doc['page_title']}")
            print()
    
    if matches_found > 0:
        print(f"✅ VERIFIED: Answer appears to use content from {matches_found} vector store document(s)")
        return True
    else:
        print("⚠️  WARNING: Could not clearly verify vector store usage")
        print("   (This might be because the model heavily paraphrased the content)")
        return False

def run_comprehensive_test(question):
    """Run complete test for a single question."""
    print("\n" + "="*80)
    print(f"🧪 COMPREHENSIVE TEST")
    print("="*80)
    print(f"Question: {question}")
    print("="*80 + "\n")
    
    # Step 1: Get vector retrieval results
    retrieved_docs = get_vector_retrieval(question, k=5)
    
    time.sleep(1)  # Small delay between calls
    
    # Step 2: Get chatbot answer
    answer = get_chatbot_answer(question)
    
    # Step 3: Verify vector usage
    if retrieved_docs and answer:
        verify_vector_usage(retrieved_docs, answer)
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")
    
    return {
        'question': question,
        'retrieved_docs': retrieved_docs,
        'answer': answer
    }

def main():
    """Run tests for all questions."""
    print("\n" + "🚀" * 40)
    print("VECTOR RETRIEVAL TESTING SUITE")
    print("🚀" * 40 + "\n")
    
    results = []
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{'#'*80}")
        print(f"TEST {i}/{len(TEST_QUESTIONS)}")
        print(f"{'#'*80}\n")
        
        result = run_comprehensive_test(question)
        results.append(result)
        
        if i < len(TEST_QUESTIONS):
            print("\n⏳ Waiting 2 seconds before next test...\n")
            time.sleep(2)
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Total questions tested: {len(results)}")
    successful = sum(1 for r in results if r['answer'] is not None)
    print(f"Successful responses: {successful}/{len(results)}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

