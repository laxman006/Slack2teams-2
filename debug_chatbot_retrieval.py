"""
Debug what the chatbot is actually retrieving and seeing
"""
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import OpenAIEmbeddings
from app.mongodb_vectorstore import MongoDBVectorStore
from config import MONGODB_VECTORSTORE_COLLECTION, SYSTEM_PROMPT
import os

def debug_retrieval():
    """Debug the full retrieval and formatting process."""
    
    print("\n" + "="*80)
    print("DEBUGGING CHATBOT RETRIEVAL")
    print("="*80 + "\n")
    
    question = "What are Multi User Golden Image Combinations?"
    
    # Initialize embeddings and vectorstore (same as chatbot)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    vectorstore = MongoDBVectorStore(
        collection_name=MONGODB_VECTORSTORE_COLLECTION,
        embedding_function=embeddings
    )
    
    print(f"Question: {question}\n")
    print("="*80)
    print("STEP 1: RETRIEVAL")
    print("="*80 + "\n")
    
    # Retrieve documents (same as chatbot does - it retrieves 25!)
    docs = vectorstore.similarity_search(question, k=25)
    
    print(f"Retrieved {len(docs)} documents:\n")
    
    for i, doc in enumerate(docs, 1):
        print(f"{i}. Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"   Type: {doc.metadata.get('source_type', 'Unknown')}")
        print(f"   Title: {doc.metadata.get('page_title', 'N/A')}")
        print(f"   Content length: {len(doc.page_content)} chars")
        print(f"   Preview: {doc.page_content[:150]}...")
        print()
    
    print("="*80)
    print("STEP 2: FORMATTING (what LLM sees)")
    print("="*80 + "\n")
    
    # Format documents (same as chatbot does)
    def format_docs(docs):
        """Format documents with source citations."""
        formatted_parts = []
        for i, doc in enumerate(docs, 1):
            metadata = doc.metadata
            file_name = metadata.get('file_name', metadata.get('source', 'Unknown'))
            source_info = f"[Document {i}] (Source: {file_name})"
            formatted_parts.append(f"{source_info}\n{doc.page_content}")
        return "\n\n---\n\n".join(formatted_parts)
    
    formatted_context = format_docs(docs)
    
    print(f"Formatted context length: {len(formatted_context)} chars\n")
    print("First 1000 chars of formatted context:")
    print("-"*80)
    print(formatted_context[:1000])
    print("-"*80)
    
    print("\n" + "="*80)
    print("STEP 3: SYSTEM PROMPT CHECK")
    print("="*80 + "\n")
    
    # Check if system prompt has the critical instruction
    if "MUST ONLY use information from the retrieved documents" in SYSTEM_PROMPT:
        print("✅ System prompt has strict instruction")
    else:
        print("⚠️  System prompt might be too strict")
    
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80 + "\n")
    
    sharepoint_docs = [d for d in docs if d.metadata.get('source') == 'cloudfuze_doc360']
    blog_docs = [d for d in docs if d.metadata.get('source') == 'cloudfuze_blog']
    
    print(f"SharePoint documents retrieved: {len(sharepoint_docs)}")
    print(f"Blog documents retrieved: {len(blog_docs)}")
    
    if len(sharepoint_docs) > 0:
        print("\n✅ SharePoint content IS being retrieved!")
        print("   The issue is likely in how the LLM interprets the content.")
    else:
        print("\n❌ SharePoint content is NOT being retrieved!")
        print("   The issue is in the similarity search.")

if __name__ == "__main__":
    debug_retrieval()

