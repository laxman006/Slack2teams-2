"""Quick test for confident responses."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from config import OPENAI_API_KEY, CHROMA_DB_PATH, SYSTEM_PROMPT
from app.llm import format_docs

# Initialize
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.3, max_tokens=500)

# Test the 2 questions that were too conservative
test_queries = [
    "combinations to migrate from object to cloud storage",
    "gmail to outlook migration"
]

for query in test_queries:
    print("\n" + "="*80)
    print(f"QUERY: {query}")
    print("="*80)
    
    # Retrieve and format documents
    doc_results = vectorstore.similarity_search_with_score(query, k=10)
    docs = [doc for doc, score in doc_results]
    
    print(f"\n[*] Top 3 documents:")
    for i, (doc, score) in enumerate(doc_results[:3], 1):
        print(f"{i}. {doc.metadata.get('file_name', 'Unknown')} (score: {score:.4f})")
    
    # Format and generate response
    formatted_docs = format_docs(docs[:5])
    context_text = "\n\n".join([f"Document {i+1}:\n{formatted_doc}" for i, formatted_doc in enumerate(formatted_docs)])
    
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

print("\n[OK] Test complete!")

