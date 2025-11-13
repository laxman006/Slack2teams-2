
import hashlib
from langchain_openai import ChatOpenAI
from config import SYSTEM_PROMPT
from app.ngram_retrieval import (
    detect_technical_ngrams,
    rerank_documents_with_ngrams,
    get_ngram_diagnostics,
    is_technical_query,
    expand_technical_query
)


def format_docs(docs):
    """
    Format documents with clean, minimal metadata.
    Optimized for LLM context efficiency (5-8 docs, 12k-15k chars max).
    """
    formatted = []
    
    for doc in docs:
        # Clean and truncate content (prevent massive PDFs from dominating context)
        content = (doc.page_content or "")[:3000]  # Max 3k chars per doc
        metadata = doc.metadata or {}
        
        # Determine document type and create clean header
        source_type = metadata.get('source_type', '').lower()
        
        if source_type == 'sharepoint':
            # SharePoint: show page title only (cleanest format)
            title = metadata.get('page_title') or metadata.get('file_name', 'SharePoint Document')
            header = f"[SharePoint: {title}]"
        elif source_type in ('web', 'blog') or metadata.get('is_blog_post'):
            # Blog: show post title
            title = metadata.get('post_title', 'Blog Post')
            header = f"[Blog: {title}]"
        elif source_type in ('pdf', 'doc', 'docx'):
            # Local files: show filename
            filename = metadata.get('source', 'Document')
            header = f"[{source_type.upper()}: {filename}]"
        elif source_type in ('excel', 'csv'):
            # Excel: show filename
            filename = metadata.get('source', 'Spreadsheet')
            header = f"[Excel: {filename}]"
        else:
            # Generic fallback
            source = metadata.get('source', 'Unknown')
            header = f"[Document: {source}]"
        
        # Combine header + content (no noisy metadata)
        formatted_content = f"{header}\n{content}"
        
        # Optional: Add download/video links if present (minimal format)
        if metadata.get("download_url"):
            formatted_content += f"\n[Download: {metadata['download_url']}]"
        if metadata.get("video_url"):
            formatted_content += f"\n[Video: {metadata['video_url']}]"
        if metadata.get("post_url"):
            formatted_content += f"\n[Full Post: {metadata['post_url']}]"
        
        formatted.append(formatted_content)
    
    return formatted


def setup_qa_chain(retriever):
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    
    # Create a custom prompt template with system message
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Context: {context}\n\nQuestion: {question}")
    ])
    
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",  # Updated model name
        streaming=False,  # Disabled - this chain uses synchronous .invoke()
        temperature=0.3,  # Balanced temperature for good responses
        max_tokens=1500   # Allow longer responses for comprehensive answers
    )
    
    # Create the document chain using the new langchain 1.x approach
    # Use the module-level format_docs function
    
    document_chain = prompt_template | llm | StrOutputParser()
    
    # Create a wrapper to maintain compatibility with the existing interface
    class SemanticRetrievalQA:
        def __init__(self, document_chain, retriever):
            self.document_chain = document_chain
            self.retriever = retriever
        
        def invoke(self, inputs):
            # Extract the query from the inputs dict
            query = inputs.get("query", "")
            
            # Get relevant documents using pure semantic search
            from app.vectorstore import vectorstore
            from app.unified_retrieval import unified_retrieve
            from app.helpers import normalize_chain_output
            
            # CRITICAL: Check if vectorstore is available
            if vectorstore is None:
                print("[ERROR] Vectorstore not initialized - cannot retrieve documents")
                class Response:
                    def __init__(self, content):
                        self.content = content
                return Response("I apologize, but the knowledge base is not currently available. Please contact support.")
            
            # Get reranked documents from unified retrieval
            docs_with_sim = unified_retrieve(query, vectorstore, bm25_retriever=None, k=50)
            
            # Extract just the documents (discard similarity scores)
            docs = [doc for doc, _ in docs_with_sim]
            
            # Format and create context
            context = "\n\n".join(format_docs(docs))
            
            # Invoke the LLM chain and normalize output
            raw = self.document_chain.invoke({
                "context": context,
                "question": query
            })
            answer_text = normalize_chain_output(raw)
            
            # Return in same format as LangChain chains (object with .content)
            class Response:
                def __init__(self, content):
                    self.content = content
            
            return Response(answer_text)
    
    qa_chain = SemanticRetrievalQA(document_chain, retriever)
    return qa_chain
