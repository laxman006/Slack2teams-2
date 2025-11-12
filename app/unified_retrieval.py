"""
Unified Retrieval Pipeline
===========================

Production-ready retrieval that replaces intent-based branching with:
- Unified hybrid search (BM25 + Vector + N-gram)
- Metadata-based soft boosting (not hard filtering)
- Automatic keyword and technical phrase detection
- Scalable to 50K+ documents without retraining

This architecture follows modern RAG best practices used by ChatGPT Enterprise,
Perplexity, and Cohere Command-R.
"""

from typing import List, Tuple, Dict, Any
from app.ngram_retrieval import (
    detect_technical_ngrams,
    score_document_for_ngrams,
    get_query_technical_score,
    is_technical_query
)


def unified_retrieve(
    query: str,
    vectorstore,
    bm25_retriever=None,
    k: int = 50,
    max_tokens: int = 4000
) -> List[Tuple[Any, float]]:
    """
    Unified retrieval pipeline that searches entire knowledge base.
    
    Args:
        query: User query
        vectorstore: Vector database (Chroma/FAISS)
        bm25_retriever: Optional BM25 retriever for hybrid search
        k: Number of documents to retrieve
        max_tokens: Maximum context tokens (for future compression)
    
    Returns:
        List of (document, score) tuples, sorted by relevance
    """
    print(f"\n{'='*70}")
    print(f"[UNIFIED RETRIEVAL] Query: {query}")
    print('='*70)
    
    # Step 1: Detect technical keywords and phrases
    detected_ngrams, ngram_weights = detect_technical_ngrams(query)
    is_tech = is_technical_query(query)
    tech_score = get_query_technical_score(query)
    
    print(f"[KEYWORDS] Detected: {detected_ngrams}")
    print(f"[TECHNICAL] Is technical query: {is_tech} (score: {tech_score:.2f})")
    
    # Step 2: Hybrid retrieval (Vector + BM25)
    all_docs = []
    
    # Vector search
    try:
        vector_results = vectorstore.similarity_search_with_score(query, k=k*2)
        all_docs.extend(vector_results)
        print(f"[VECTOR] Retrieved {len(vector_results)} documents")
    except Exception as e:
        print(f"[VECTOR] Error: {e}")
        vector_results = []
    
    # BM25 search (if available)
    if bm25_retriever:
        try:
            bm25_results = bm25_retriever.get_relevant_documents(query)
            # Add with default score
            bm25_docs = [(doc, 0.5) for doc in bm25_results[:k]]
            all_docs.extend(bm25_docs)
            print(f"[BM25] Retrieved {len(bm25_results)} documents")
        except Exception as e:
            print(f"[BM25] Error: {e}")
    
    # CRITICAL: Add targeted SharePoint search for technical queries
    # This ensures SharePoint technical docs are always considered
    if is_tech and detected_ngrams:
        try:
            # Create a search query with detected technical terms
            sharepoint_query = " ".join(detected_ngrams[:5])  # Top 5 keywords
            sharepoint_results = vectorstore.similarity_search_with_score(
                f"{sharepoint_query} documentation guide",
                k=20  # Get 20 more docs
            )
            # Filter for SharePoint docs only
            sharepoint_docs = [
                (doc, score * 0.7)  # Give them a boost (multiply score by 0.7 = lower score = better)
                for doc, score in sharepoint_results
                if doc.metadata.get('source_type') == 'sharepoint'
            ]
            if sharepoint_docs:
                all_docs.extend(sharepoint_docs)
                print(f"[SHAREPOINT] Added {len(sharepoint_docs)} targeted SharePoint documents")
        except Exception as e:
            print(f"[SHAREPOINT] Error: {e}")
    
    if not all_docs:
        print("[WARNING] No documents retrieved!")
        return []
    
    # Step 3: Deduplicate
    seen = set()
    unique_docs = []
    for doc, score in all_docs:
        doc_id = id(doc) if hasattr(doc, '__hash__') else hash(doc.page_content[:100])
        if doc_id not in seen:
            seen.add(doc_id)
            unique_docs.append((doc, score))
    
    print(f"[DEDUP] {len(all_docs)} → {len(unique_docs)} unique documents")
    
    # Step 4: Apply smart reranking
    reranked_docs = rerank_with_metadata_and_ngrams(
        unique_docs,
        query,
        detected_ngrams,
        ngram_weights,
        is_tech
    )
    
    # Step 5: Limit to top k
    final_docs = reranked_docs[:k]
    
    print(f"[FINAL] Returning top {len(final_docs)} documents")
    print(f"[TOP 3 SCORES] {[f'{score:.3f}' for _, score in final_docs[:3]]}")
    print('='*70)
    
    return final_docs


def rerank_with_metadata_and_ngrams(
    docs: List[Tuple[Any, float]],
    query: str,
    detected_ngrams: List[str],
    ngram_weights: Dict[str, float],
    is_tech: bool
) -> List[Tuple[Any, float]]:
    """
    Rerank documents using metadata + N-gram boosting.
    
    This is the CORE intelligence - replaces intent classification with smart,
    automatic relevance detection.
    """
    query_lower = query.lower()
    scored_docs = []
    
    for doc, base_score in docs:
        # Start with base score (lower is better for similarity)
        final_score = base_score
        
        # Extract metadata
        metadata = doc.metadata
        content_lower = doc.page_content.lower()
        source = metadata.get('source', '')
        tag = metadata.get('tag', '').lower()
        source_type = metadata.get('source_type', '').lower()
        
        # ===== METADATA-BASED SOFT BOOSTING =====
        
        # Boost SharePoint documents for SharePoint queries
        if 'sharepoint' in query_lower and source_type == 'sharepoint':
            final_score *= 0.7  # 30% boost
        
        # Boost blog posts for general questions
        if 'blog' in tag and not is_tech:
            final_score *= 0.85  # 15% boost
        
        # Boost technical docs for technical queries
        if is_tech and any(t in tag for t in ['technical', 'api', 'developer']):
            final_score *= 0.75  # 25% boost
        
        # ===== SHAREPOINT DOCUMENT TITLE/FILENAME BOOST =====
        
        # CRITICAL: Strong boost for SharePoint docs with filenames matching query
        file_name = metadata.get('file_name', '').lower()
        if file_name and source_type == 'sharepoint':
            # Check if query terms appear in filename
            query_words = [w.lower() for w in query.split() if len(w) > 3]
            filename_matches = sum(1 for word in query_words if word in file_name)
            
            if filename_matches >= 3:  # If 3+ query words in filename
                final_score *= 0.3  # MASSIVE 70% boost - prioritize exact file matches!
                print(f"[BOOST] SharePoint file '{file_name}' matches {filename_matches} query terms - strong boost applied")
            elif filename_matches >= 2:
                final_score *= 0.5  # 50% boost
        
        # ===== KEYWORD MATCHING BOOST =====
        
        # Extract key query terms (simple but effective)
        query_terms = [term for term in query_lower.split() if len(term) > 3]
        matched_terms = sum(1 for term in query_terms if term in content_lower)
        
        if matched_terms > 0:
            # Boost based on term overlap
            term_boost = 1.0 - (matched_terms * 0.05)  # Up to 50% boost for 10+ terms
            final_score *= max(term_boost, 0.5)
        
        # ===== N-GRAM BOOSTING =====
        
        if is_tech and detected_ngrams:
            # Calculate N-gram relevance score for this document
            ngram_score = score_document_for_ngrams(
                doc.page_content,
                metadata,
                detected_ngrams,
                ngram_weights
            )
            
            if ngram_score > 0:
                # Convert ngram score to boost (higher ngram score = better document)
                # Scale: ngram_score of 5.0 = 40% boost
                ngram_boost = 1.0 - (min(ngram_score, 10.0) * 0.04)
                final_score *= ngram_boost
        
        # ===== DETECTED KEYWORD EXACT MATCH BOOST =====
        
        # Strong boost for documents containing detected keywords
        keyword_matches = sum(1 for kw in detected_ngrams if kw in content_lower)
        if keyword_matches > 0:
            keyword_boost = 0.8 ** keyword_matches  # Exponential boost
            final_score *= keyword_boost
        
        scored_docs.append((doc, final_score))
    
    # Sort by final score (lower is better)
    scored_docs.sort(key=lambda x: x[1])
    
    return scored_docs


def extract_query_keywords(query: str, min_length: int = 3) -> List[str]:
    """
    Extract important keywords from query.
    Simple but effective approach.
    """
    # Common stop words to skip
    stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'or', 'but', 
                  'what', 'how', 'when', 'where', 'who', 'why', 'does',
                  'do', 'did', 'will', 'would', 'could', 'should', 'can',
                  'has', 'have', 'had', 'been', 'being', 'are', 'was', 'were',
                  'for', 'with', 'about', 'from', 'into', 'through', 'during'}
    
    words = query.lower().split()
    keywords = [w for w in words if len(w) >= min_length and w not in stop_words]
    
    return keywords


def create_unified_prompt(context_docs: List[Any], query: str) -> str:
    """
    Create unified prompt that works for all query types.
    
    This replaces per-intent prompts with a single, flexible prompt.
    """
    # Format documents
    formatted_context = []
    
    for i, doc in enumerate(context_docs, 1):
        content = doc.page_content
        metadata = doc.metadata
        
        # Add source attribution
        source = metadata.get('source', 'Unknown')
        tag = metadata.get('tag', 'general')
        
        # Format based on content type
        if metadata.get('source_type') == 'sharepoint':
            file_name = metadata.get('file_name', '')
            formatted_context.append(f"[Document {i} - {tag} - {file_name}]\n{content}")
        else:
            formatted_context.append(f"[Document {i} - {tag}]\n{content}")
    
    context_text = "\n\n---\n\n".join(formatted_context)
    
    # Create unified prompt
    prompt = f"""You are a CloudFuze knowledge assistant. Answer the user's question based on the provided context.

The context may include information from:
- Migration guides (Slack, Teams, SharePoint, OneDrive)
- Technical documentation (APIs, JSON formats, metadata)
- Product features and capabilities
- Security and compliance information
- Blog posts and articles

Context:
{context_text}

User Question: {query}

Instructions:
- Answer directly and specifically based on the context
- Include relevant technical details when available
- Mention specific document names, features, or processes when referenced
- If the context doesn't contain enough information, say so clearly
- Maintain a professional, helpful tone

Answer:"""
    
    return prompt


# ===== HELPER: Get retriever (for use in endpoints.py) =====

def get_unified_retriever(vectorstore, bm25_retriever=None):
    """
    Factory function to create a unified retriever.
    
    Usage in endpoints.py:
        retriever = get_unified_retriever(vectorstore, bm25_retriever)
        docs = retriever(query, k=50)
    """
    def retrieve(query: str, k: int = 50):
        return unified_retrieve(query, vectorstore, bm25_retriever, k)
    
    return retrieve

