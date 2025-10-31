
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
    def format_docs(docs):
        """Format documents with source citations for better LLM responses."""
        formatted_parts = []
        
        for i, doc in enumerate(docs, 1):
            # Extract metadata
            metadata = doc.metadata
            file_name = metadata.get('file_name', metadata.get('source', 'Unknown'))
            folder_path = metadata.get('folder_path', '')
            file_type = metadata.get('file_type', '')
            last_modified = metadata.get('last_modified', '')
            page_number = metadata.get('page_number', '')
            
            # Build source citation
            source_info = f"[Document {i}]"
            
            if file_name != 'Unknown':
                source_info += f" (Source: {file_name}"
                
                # Add folder path for SharePoint documents
                if folder_path:
                    source_info += f" - {folder_path}"
                
                # Add page number for PDFs if available
                if page_number:
                    source_info += f", Page {page_number}"
                
                # Add last modified date if recent
                if last_modified:
                    try:
                        from datetime import datetime
                        # Parse and format date
                        modified_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                        date_str = modified_date.strftime('%Y-%m-%d')
                        source_info += f", Modified: {date_str}"
                    except:
                        pass
                
                source_info += ")"
            
            # Combine source info with content
            formatted_parts.append(f"{source_info}\n{doc.page_content}")
        
        return "\n\n---\n\n".join(formatted_parts)
    
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
            context = format_docs(final_docs)
            
            # Invoke the document chain with the semantically relevant documents
            result = self.document_chain.invoke({
                "context": context,
                "question": query
            })
            
            return {"result": result}
    
    qa_chain = SemanticRetrievalQA(document_chain, retriever)
    return qa_chain
