
import asyncio
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_openai import ChatOpenAI
# RetrievalQA is now handled differently in langchain 1.x
from config import SYSTEM_PROMPT


class AsyncStreamHandler(BaseCallbackHandler):
    def __init__(self):
        self.queue = asyncio.Queue()

    def on_llm_new_token(self, token: str, **kwargs):
        self.queue.put_nowait(token)


def format_docs(docs):
    """Format documents with their content and metadata (especially download URLs, video URLs, and tags)."""
    formatted = []
    sources_used = []
    
    for doc in docs:
        content = doc.page_content
        metadata = doc.metadata
        
        # Track source information for logging
        source = metadata.get('source', 'Unknown')
        tag = metadata.get("tag", "unknown")
        sources_used.append(f"{source} ({tag})")
        
        # Include tag information in context (for chatbot to know data source)
        tag_info = f"[SOURCE: {tag}]"
        
        # For SharePoint documents, add additional context for better understanding
        if metadata.get("source_type") == "sharepoint":
            file_name = metadata.get('file_name', '')
            folder_path = metadata.get('folder_path', '')
            if file_name:
                content = f"{tag_info}\nFile: {file_name}\nFolder: {folder_path}\n\n{content}"
        else:
            content = f"{tag_info}\n{content}"
        
        # Include download URL for certificates and downloadable files (policy documents, etc.) in the context
        if metadata.get("is_downloadable") and metadata.get("download_url"):
            file_name = metadata.get('file_name', 'File')
            download_url = metadata.get('download_url')
            is_cert = metadata.get('is_certificate', False)
            # Escape any curly braces that might interfere with string formatting
            file_name_escaped = file_name.replace('{', '{{').replace('}', '}}')
            download_url_escaped = download_url.replace('{', '{{').replace('}', '}}')
            content += f"\n\n[DOWNLOAD LINK: {file_name_escaped} (is_certificate: {is_cert}, is_downloadable: True) - {download_url_escaped}]"
        
        # Include video URL for demo videos in the context
        if metadata.get("content_type") == "sharepoint_video" and metadata.get("video_url"):
            video_name = metadata.get("video_name") or metadata.get("file_name", "Video")
            video_url = metadata.get("video_url")
            video_type = metadata.get("video_type", "video")
            # Escape any curly braces that might interfere with string formatting
            video_name_escaped = video_name.replace('{', '{{').replace('}', '}}')
            video_url_escaped = video_url.replace('{', '{{').replace('}', '}}')
            content += f"\n\n[VIDEO LINK: {video_name_escaped} ({video_type}) - {video_url_escaped}]"
        
        formatted.append(content)
    
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
        streaming=True, 
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
            
            # PURE SEMANTIC SEARCH - Let the vectorstore handle semantic understanding
            # No predefined keywords, no hardcoded terms, no forced inclusions
            
            # Primary semantic search with the original query
            relevant_docs = vectorstore.similarity_search(query, k=25)
            
            # Secondary semantic search with query rephrasing for better coverage
            # This helps catch semantically similar but differently worded content
            try:
                # Use the LLM to create a semantic variation of the query
                rephrase_prompt = f"""
                Rephrase this question in 2-3 different ways to help find relevant information:
                Original: {query}
                
                Provide 2-3 alternative phrasings that mean the same thing but use different words.
                Each rephrasing should be on a new line and be concise.
                """
                
                rephrase_result = llm.invoke(rephrase_prompt)
                rephrased_queries = [line.strip() for line in rephrase_result.content.split('\n') if line.strip()]
                
                # Search with each rephrased query
                for rephrased_query in rephrased_queries[:2]:  # Limit to 2 rephrasings
                    additional_docs = vectorstore.similarity_search(rephrased_query, k=12)
                    relevant_docs.extend(additional_docs)
                    
            except Exception as e:
                # If rephrasing fails, continue with original query only
                print(f"Query rephrasing failed: {e}")
                pass
            
            # Deduplicate documents while preserving relevance order
            seen_ids = set()
            unique_docs = []
            
            for doc in relevant_docs:
                # Create a unique identifier for the document
                doc_id = f"{doc.metadata.get('source', '')}_{doc.page_content[:50]}"
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    unique_docs.append(doc)
            
            # Limit to reasonable number of documents for processing
            # Too many documents can overwhelm the LLM and reduce quality
            final_docs = unique_docs[:30]
            
            # Format the documents for the context
            formatted_docs = format_docs(final_docs)
            context = "\n\n".join(formatted_docs)
            
            # Invoke the document chain with the semantically relevant documents
            result = self.document_chain.invoke({
                "context": context,
                "question": query
            })
            
            return {"result": result}
    
    qa_chain = SemanticRetrievalQA(document_chain, retriever)
    return qa_chain
