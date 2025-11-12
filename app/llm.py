
import asyncio
import hashlib
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_openai import ChatOpenAI
# RetrievalQA is now handled differently in langchain 1.x
from config import SYSTEM_PROMPT
from app.ngram_retrieval import (
    detect_technical_ngrams,
    rerank_documents_with_ngrams,
    get_ngram_diagnostics,
    is_technical_query,
    expand_technical_query
)


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
        
        # Include blog post URL for blog content in the context
        if metadata.get("is_blog_post") and metadata.get("post_url"):
            post_title = metadata.get('post_title', 'Blog Post')
            post_url = metadata.get('post_url')
            # Escape any curly braces that might interfere with string formatting
            post_title_escaped = post_title.replace('{', '{{').replace('}', '}}')
            post_url_escaped = post_url.replace('{', '{{').replace('}', '}}')
            content += f"\n\n[BLOG POST LINK: {post_title_escaped} - {post_url_escaped}]"
        
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
            user_id = inputs.get("user_id") or inputs.get("metadata", {}).get("user_id")
            
            # Get conversation context if user_id provided
            user_context = ""
            if user_id:
                try:
                    # Try async mongodb memory first
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is already running, we can't use asyncio.run
                        # Fall back to synchronous memory or skip
                        print(f"[CONTEXT] Event loop already running, skipping context injection")
                    else:
                        from app.mongodb_memory import get_conversation_context
                        user_context = loop.run_until_complete(get_conversation_context(user_id))
                        if user_context:
                            print(f"[CONTEXT] Injected conversation history for user {user_id}")
                except Exception as e:
                    print(f"[CONTEXT] Failed to get conversation context: {e}")
            
            # Enhance query with conversation context if available
            query_with_history = f"{user_context}\n\nCurrent question: {query}" if user_context else query
            
            # Get relevant documents using pure semantic search
            from app.vectorstore import vectorstore
            
            # ================================================================
            # HYBRID RETRIEVAL: Semantic Search + N-gram Boosting
            # ================================================================
            
            # Step 1: Detect technical n-grams in the query (use enhanced query for detection)
            detected_ngrams, ngram_weights = detect_technical_ngrams(query_with_history)
            is_tech_query = is_technical_query(query_with_history)
            
            print(f"[N-GRAM DETECTION] Query: {query}")
            print(f"[N-GRAM DETECTION] Technical keywords detected: {detected_ngrams}")
            print(f"[N-GRAM DETECTION] Is technical: {is_tech_query}")
            
            # Step 2: Primary semantic search - EXPAND query with detected keywords
            # This helps the vector search focus on documents with these technical terms
            if detected_ngrams:
                # Add detected keywords to boost vector similarity
                keyword_expansion = " ".join(detected_ngrams[:5])  # Limit to top 5 to avoid query dilution
                expanded_search_query = f"{query_with_history} {keyword_expansion}"
                print(f"[N-GRAM BOOST] Expanding search query with keywords: {keyword_expansion}")
                relevant_docs = vectorstore.similarity_search(expanded_search_query, k=25)
            else:
                relevant_docs = vectorstore.similarity_search(query_with_history, k=25)
            
            # Step 3: If technical query, expand with technical variations
            if is_tech_query:
                print(f"[N-GRAM BOOST] Applying technical query expansion...")
                expanded_queries = expand_technical_query(query)
                
                # Search with expanded queries
                for expanded_query in expanded_queries[1:3]:  # Skip first (original), limit to 2 expansions
                    print(f"[N-GRAM BOOST] Expanded query: {expanded_query}")
                    additional_docs = vectorstore.similarity_search(expanded_query, k=10)
                    relevant_docs.extend(additional_docs)
            else:
                # For non-technical queries, use LLM rephrasing
                try:
                    # Use the LLM to create a semantic variation of the query
                    rephrase_prompt = f"""
                    Rephrase this question in 2-3 different ways to help find relevant information:
                    Original: {query}
                    
                    Provide 2-3 alternative phrasings that mean the same thing but use different words.
                    Each rephrasing should be on a new line and be concise.
                    """
                    
                    rephrase_output = llm.invoke(rephrase_prompt)
                    # Safe extraction of text from LLM response
                    rephrase_text = ""
                    if hasattr(rephrase_output, "content"):
                        rephrase_text = rephrase_output.content
                    elif isinstance(rephrase_output, str):
                        rephrase_text = rephrase_output
                    else:
                        try:
                            rephrase_text = str(rephrase_output)
                        except:
                            rephrase_text = ""
                    
                    rephrased_queries = [line.strip() for line in rephrase_text.split('\n') if line.strip()]
                    
                    # Search with each rephrased query
                    for rephrased_query in rephrased_queries[:2]:  # Limit to 2 rephrasings
                        additional_docs = vectorstore.similarity_search(rephrased_query, k=12)
                        relevant_docs.extend(additional_docs)
                        
                except Exception as e:
                    # If rephrasing fails, continue with original query only
                    print(f"[LLM REPHRASE] Failed: {e}")
                    pass
            
            # Deduplicate documents while preserving relevance order
            # Using hash of source + larger content window for better uniqueness
            seen_ids = set()
            unique_docs = []
            
            for doc in relevant_docs:
                # Create a unique identifier using hash of source + first 500 chars
                doc_key = (doc.metadata.get('source', '') + doc.page_content[:500])
                doc_id = hashlib.md5(doc_key.encode('utf-8')).hexdigest()
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    unique_docs.append(doc)
            
            # Step 4: Apply N-gram reranking if technical query detected
            MAX_CONTEXT_DOCS = 10  # Limit context to top 10 docs to prevent overload
            
            if is_tech_query and detected_ngrams:
                print(f"[N-GRAM BOOST] Reranking {len(unique_docs)} documents with n-gram boosting...")
                
                # Rerank documents based on n-gram matching (use original query, not history-enhanced)
                reranked_docs = rerank_documents_with_ngrams(unique_docs, query)
                
                # Extract documents from scored tuples and log scores
                final_docs = []
                for doc, score in reranked_docs[:MAX_CONTEXT_DOCS]:  # Take top N after reranking
                    final_docs.append(doc)
                    # Log top documents for debugging
                    if len(final_docs) <= 5:
                        source = doc.metadata.get('source', 'Unknown')[:50]
                        tag = doc.metadata.get('tag', 'unknown')
                        print(f"[N-GRAM BOOST] Top doc #{len(final_docs)}: score={score:.2f}, tag={tag}, source={source}")
            else:
                # No technical n-grams, use original order
                final_docs = unique_docs[:MAX_CONTEXT_DOCS]
                print(f"[N-GRAM BOOST] No technical n-grams detected, using semantic order")
            
            print(f"[CONTEXT] Using {len(final_docs)} documents for LLM context")
            
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
