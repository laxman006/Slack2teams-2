"""Test script to check chatbot document retrieval and responses."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from config import OPENAI_API_KEY, CHROMA_DB_PATH, SYSTEM_PROMPT
from app.llm import format_docs

# Initialize embeddings
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# Load vectorstore
print("[*] Loading vectorstore...")
try:
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings
    )
    print("[OK] Vectorstore loaded")
except Exception as e:
    print(f"[ERROR] Failed to load vectorstore: {e}")
    sys.exit(1)

# Test queries
test_queries = [
    "What is CloudFuze?",
    "How do I migrate from Box to SharePoint?",
    "What migration guides are available?",
    "Download SOC 2 certificate",
    "What policy documents do you have?",
    "combinations to migrate from object to cloud storage",
    "gmail to outlook?"
]

# Initialize LLM for generating responses
llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0.3,
    max_tokens=500  # Shorter for testing
)

def test_query(query):
    print("\n" + "="*80)
    print(f"QUERY: {query}")
    print("="*80)
    
    # Retrieve documents
    print(f"\n[*] Retrieving documents for: '{query}'")
    doc_results = vectorstore.similarity_search_with_score(query, k=10)
    
    if not doc_results:
        print("[WARNING] No documents retrieved!")
        return
    
    docs = [doc for doc, score in doc_results]
    
    # Show retrieved documents
    print(f"\n[*] Retrieved {len(docs)} documents:")
    for i, (doc, score) in enumerate(doc_results[:5], 1):
        print(f"\n{i}. Score: {score:.4f}")
        print(f"   Source Type: {doc.metadata.get('source_type', 'unknown')}")
        print(f"   Tag: {doc.metadata.get('tag', 'unknown')}")
        if doc.metadata.get('source_type') == 'sharepoint':
            print(f"   File: {doc.metadata.get('file_name', 'N/A')}")
            print(f"   Folder: {doc.metadata.get('folder_path', 'N/A')}")
        print(f"   Content preview: {doc.page_content[:150]}...")
    
    # Format documents
    print(f"\n[*] Formatting documents with metadata...")
    try:
        formatted_docs = format_docs(docs[:5])  # Format top 5
        context_text = "\n\n".join([f"Document {i+1}:\n{formatted_doc}" for i, formatted_doc in enumerate(formatted_docs)])
        print(f"[OK] Context length: {len(context_text)} characters")
        print(f"\n[*] Context preview (first 800 chars):")
        print("-" * 80)
        print(context_text[:800])
        print("-" * 80)
    except Exception as e:
        print(f"[ERROR] Failed to format documents: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Generate response
    print(f"\n[*] Generating response...")
    try:
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Context: {context}\n\nQuestion: {question}")
        ])
        
        messages = prompt_template.format_messages(context=context_text, question=query)
        response = llm.invoke(messages)
        
        print(f"\n[*] RESPONSE:")
        print("-" * 80)
        print(response.content)
        print("-" * 80)
        
    except Exception as e:
        print(f"[ERROR] Failed to generate response: {e}")
        import traceback
        traceback.print_exc()

# Run tests
print("\n" + "="*80)
print("CHATBOT TESTING - DOCUMENT RETRIEVAL AND RESPONSES")
print("="*80)

for query in test_queries:
    try:
        test_query(query)
        print("\n")
        input("Press Enter to continue to next query...")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        break
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        continue

print("\n[OK] Testing complete!")

