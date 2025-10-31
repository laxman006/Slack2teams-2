"""
Test which sources are being retrieved for SharePoint questions
"""
from langchain_openai import OpenAIEmbeddings
from app.mongodb_vectorstore import MongoDBVectorStore
from config import MONGODB_VECTORSTORE_COLLECTION
from dotenv import load_dotenv
import os

load_dotenv()

def test_retrieval(query):
    """Test what documents are retrieved for a query."""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}\n")
    
    # Initialize embeddings and vectorstore
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    vectorstore = MongoDBVectorStore(
        collection_name=MONGODB_VECTORSTORE_COLLECTION,
        embedding_function=embeddings
    )
    
    # Retrieve top 5 documents
    results = vectorstore.similarity_search(query, k=5)
    
    print(f"Retrieved {len(results)} documents:\n")
    
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get('source', 'Unknown')
        source_type = doc.metadata.get('source_type', 'Unknown')
        page_title = doc.metadata.get('page_title', 'N/A')
        page_url = doc.metadata.get('page_url', 'N/A')
        
        print(f"{i}. Source: {source}")
        print(f"   Type: {source_type}")
        if source == 'cloudfuze_doc360':
            print(f"   Title: {page_title}")
            print(f"   URL: {page_url}")
        print(f"   Preview: {doc.page_content[:150]}...")
        print()

# Test queries
queries = [
    "What are Multi User Golden Image Combinations?",
    "Slack to Teams migration",
    "Box to OneDrive features",
    "Message migration combinations"
]

for query in queries:
    test_retrieval(query)

