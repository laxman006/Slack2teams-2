# -*- coding: utf-8 -*-
"""
Langfuse Integration for RAG Chatbot Observability

This module handles logging all chat interactions to Langfuse for observability.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from langfuse import Langfuse
from config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST

# Initialize Langfuse client
try:
    if not LANGFUSE_SECRET_KEY or not LANGFUSE_PUBLIC_KEY:
        print("[!] Langfuse credentials not found - observability disabled")
        langfuse_client = None
    else:
        langfuse_client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST
        )
        print(f"[OK] Langfuse initialized: {LANGFUSE_HOST}")
except Exception as e:
    print(f"[!] Langfuse initialization failed: {e}")
    langfuse_client = None


class LangfuseTracker:
    """Handles Langfuse trace logging"""
    
    def __init__(self):
        self.client = langfuse_client
    
    def create_trace(
        self, 
        user_id: str, 
        question: str, 
        answer: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Optional[str]:
        """Create a simple chat trace (for non-RAG queries)."""
        if not self.client:
            return None
        
        try:
            # Build metadata
            trace_metadata = {**(metadata or {}), "timestamp": datetime.now().isoformat()}
            
            trace = self.client.trace(
                name="chat_interaction",
                user_id=user_id,
                session_id=session_id or user_id,
                input=question,
                output=answer,
                metadata=trace_metadata,
                tags=["chat"]
            )
            
            trace.generation(
                name="chat_response",
                model="gpt-4o-mini",
                input=question,
                output=answer,
                metadata={"timestamp": datetime.now().isoformat()}
            )
            
            return trace.id
            
        except Exception as e:
            print(f"[ERROR] Langfuse trace failed: {e}")
            return None
    
    def add_feedback(self, trace_id: str, rating: str, comment: Optional[str] = None) -> bool:
        """Add user feedback (thumbs up/down) to a trace."""
        if not self.client:
            return False
        
        try:
            self.client.score(
                trace_id=trace_id,
                name="user_rating",
                value=1 if rating == "thumbs_up" else 0,
                comment=comment or ""
            )
            return True
            
        except Exception as e:
            print(f"[ERROR] Langfuse feedback failed: {e}")
            return False
    
    def log_observation_to_trace(
        self, 
        trace_id: str, 
        name: str, 
        input_data: Any, 
        output_data: Any, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log custom observation to existing trace (for manual corrections)."""
        if not self.client:
            return False
        
        try:
            trace = self.client.trace(id=trace_id, name="manual_correction_review")
            trace.span(
                name=name,
                input=input_data,
                output=output_data,
                metadata={**(metadata or {}), "timestamp": datetime.now().isoformat()}
            )
            return True
            
        except Exception as e:
            print(f"[ERROR] Langfuse observation failed: {e}")
            return False
    
    def create_rag_pipeline_trace(
        self, 
        user_id: str, 
        question: str, 
        session_id: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        prompt_template = None,
        prompt_metadata: Optional[Dict[str, Any]] = None
    ):
        """Create structured RAG pipeline trace with nested spans and prompt tracking."""
        if not self.client:
            return None
        
        try:
            # Build metadata with prompt info
            trace_metadata = {**(metadata or {}), "timestamp": datetime.now().isoformat()}
            
            # Add prompt metadata if provided
            if prompt_metadata:
                trace_metadata.update({
                    "prompt_name": prompt_metadata.get("prompt_name"),
                    "prompt_version": prompt_metadata.get("version"),
                    "prompt_source": prompt_metadata.get("source")
                })
            
            trace = self.client.trace(
                name="chat_interaction",
                user_id=user_id,
                session_id=session_id or user_id,
                input=question,
                metadata=trace_metadata,
                tags=["rag", "chat"]
            )
            return RAGPipelineTrace(trace, prompt_template, prompt_metadata)
            
        except Exception as e:
            print(f"[ERROR] RAG trace failed: {e}")
            return None


class RAGPipelineTrace:
    """
    RAG pipeline trace with nested spans and prompt tracking:
    chat_interaction → query → retrieve/synthesize/generating_response
    """
    
    def __init__(self, trace, prompt_template=None, prompt_metadata=None):
        self.trace = trace
        self.trace_id = trace.id
        self.query_span = None
        self.retrieve_span = None
        self.synthesize_span = None
        self.prompt_template = prompt_template  # Langfuse prompt object
        self.prompt_metadata = prompt_metadata or {}
    
    def start_query(self, enhanced_query: str, metadata: Optional[Dict[str, Any]] = None):
        """Start query processing span."""
        try:
            self.query_span = self.trace.span(
                name="query",
                input=enhanced_query,
                metadata={**(metadata or {}), "timestamp": datetime.now().isoformat()}
            )
            return self.query_span
        except Exception as e:
            print(f"[ERROR] Query span failed: {e}")
            return None
    
    def log_ngram_detection(self, query: str, detected_ngrams: list, ngram_weights: Dict[str, float], 
                           technical_score: float, is_technical: bool, metadata: Optional[Dict[str, Any]] = None):
        """Log N-gram detection and technical query classification."""
        try:
            if not self.query_span:
                print("[WARNING] Cannot log N-gram detection: query_span not started")
                return None
            
            ngram_span = self.query_span.span(
                name="ngram_detection",
                input=query,
                output={
                    "detected_ngrams": detected_ngrams,
                    "ngram_weights": ngram_weights,
                    "technical_score": technical_score,
                    "is_technical_query": is_technical,
                    "total_ngrams_detected": len(detected_ngrams)
                },
                metadata={
                    **(metadata or {}),
                    "timestamp": datetime.now().isoformat(),
                    "boost_applied": is_technical
                }
            )
            
            print(f"[LANGFUSE] Logged N-gram detection: {len(detected_ngrams)} technical phrases, score={technical_score:.2f}")
            return ngram_span
            
        except Exception as e:
            print(f"[ERROR] N-gram detection span failed: {e}")
            return None
    
    def log_ngram_reranking(self, original_doc_count: int, reranked_doc_count: int, 
                           top_docs_info: list, metadata: Optional[Dict[str, Any]] = None):
        """Log N-gram based document reranking results."""
        try:
            if not self.query_span:
                print("[WARNING] Cannot log N-gram reranking: query_span not started")
                return None
            
            reranking_span = self.query_span.span(
                name="ngram_reranking",
                input=f"Reranking {original_doc_count} documents",
                output={
                    "reranked_count": reranked_doc_count,
                    "top_documents": top_docs_info[:10]  # Log top 10 for reference
                },
                metadata={
                    **(metadata or {}),
                    "timestamp": datetime.now().isoformat(),
                    "ranking_method": "hybrid_semantic_ngram"
                }
            )
            
            print(f"[LANGFUSE] Logged N-gram reranking: {reranked_doc_count} documents reranked")
            return reranking_span
            
        except Exception as e:
            print(f"[ERROR] N-gram reranking span failed: {e}")
            return None
    
    def log_retrieval(self, query: str, retrieved_docs: list, doc_count: int, sources_breakdown: Dict[str, int], metadata: Optional[Dict[str, Any]] = None):
        """Log document retrieval with nested embedding span."""
        try:
            self.retrieve_span = self.query_span.span(
                name="retrieve",
                input=query,
                output=f"Retrieved {doc_count} documents",
                metadata={
                    **(metadata or {}),
                    "document_count": doc_count,
                    "sources_breakdown": sources_breakdown,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            self.retrieve_span.span(
                name="vectorstore_embedding",
                input=query,
                output=f"Embedded query and searched {doc_count} documents",
                metadata={"embedding_model": "text-embedding-ada-002", "timestamp": datetime.now().isoformat()}
            )
            
            return self.retrieve_span
            
        except Exception as e:
            print(f"[ERROR] Retrieval span failed: {e}")
            return None
    
    def start_synthesis(self, context: str, metadata: Optional[Dict[str, Any]] = None):
        """Start synthesis span."""
        try:
            self.synthesize_span = self.query_span.span(
                name="synthesize",
                input={"context_length": len(context)},
                metadata={**(metadata or {}), "timestamp": datetime.now().isoformat()}
            )
            return self.synthesize_span
            
        except Exception as e:
            print(f"[ERROR] Synthesis span failed: {e}")
            return None
    
    def log_llm_generation(self, prompt: str, response: str, model: str = "gpt-4o-mini", metadata: Optional[Dict[str, Any]] = None):
        """Log LLM generation span with prompt tracking."""
        try:
            generation_params = {
                "name": "openai_llm",
                "model": model,
                "input": prompt,
                "output": response,
                "metadata": {**(metadata or {}), "timestamp": datetime.now().isoformat()}
            }
            
            # If we have a Langfuse prompt template, log metadata but DON'T pass the template object
            # Passing the template object causes Langfuse SDK to compile it internally, which breaks on {curly braces} in context
            if self.prompt_template:
                # Instead of linking the template object, just add metadata about which prompt was used
                generation_params["metadata"]["prompt_name"] = self.prompt_metadata.get('prompt_name')
                generation_params["metadata"]["prompt_version"] = self.prompt_metadata.get('version')
                generation_params["metadata"]["prompt_source"] = self.prompt_metadata.get('source')
                print(f"[PROMPT] Linked prompt to generation: {self.prompt_metadata.get('prompt_name')} v{self.prompt_metadata.get('version')}")
            
            return self.synthesize_span.generation(**generation_params)
        except Exception as e:
            print(f"[ERROR] LLM generation failed: {e}")
            return None
    
    def log_response_generation(self, final_response: str, metadata: Optional[Dict[str, Any]] = None):
        """Log final response generation span."""
        try:
            return self.query_span.span(
                name="generating_response",
                input="Formatted LLM output",
                output=final_response,
                metadata={
                    **(metadata or {}),
                    "response_length": len(final_response),
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"[ERROR] Response generation failed: {e}")
            return None
    
    def complete(self, final_output: str, metadata: Optional[Dict[str, Any]] = None):
        """Complete trace with final output and metadata."""
        try:
            if self.query_span:
                self.query_span.end(output=final_output)
            
            # Update trace with output
            self.trace.update(output=final_output)
            
            # If metadata is provided, update it separately
            # Langfuse merges metadata on update, not replaces
            if metadata:
                self.trace.update(metadata=metadata)
            
            return self.trace_id
        except Exception as e:
            print(f"[ERROR] Trace completion failed: {e}")
            return self.trace_id


# Global tracker instance
langfuse_tracker = LangfuseTracker()

