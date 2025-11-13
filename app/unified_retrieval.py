# app/unified_retrieval.py
"""
Production-grade Hybrid Retrieval (ChatGPT-Enterprise style)
- Similarity-first (higher = better)
- Combines vector similarity + BM25 + phrase/metadata boosts
- Optimized for CloudFuze knowledge base structure
- Uses `source_type` for relevance (sharepoint vs. web/blog)
- NO recency weighting (removed per user request)
"""

from typing import List, Tuple, Optional, Dict, Any
import logging
import re
import math
from app.ngram_retrieval import detect_technical_ngrams, expand_technical_query

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# CONFIGURATION (tune these)
# ============================================================
DEFAULT_K = 50
MAX_RETURN = 50

# Use similarity-based weighting
SHAREPOINT_BOOST = 2.6
SHAREPOINT_DOC_EXTRA = 1.6

WEB_NEUTRAL = 1.0
WEB_PENALTY = 0.96   # keep blogs low, but still available

PHRASE_HIT_BOOST = 1.2
FILENAME_MATCH_BOOST = 1.18

FINAL_DOC_LIMIT = 50

_norm_re = re.compile(r'[^a-z0-9\s]')


# ============================================================
# NORMALIZATION HELPERS
# ============================================================
def normalize_text(t: str) -> str:
    if not t:
        return ""
    t = t.lower()
    t = _norm_re.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def _as_similarity(raw: Any) -> float:
    """
    Convert raw vectorstore score → similarity (higher = better).
    If score is between 0..1 = distance → convert via 1/(1+d).
    Otherwise assume it's already similarity-like.
    """
    try:
        s = float(raw)
    except:
        return 0.0

    if 0.0 <= s <= 1.0:
        return 1.0 / (1.0 + s)

    return s


# ============================================================
# SOURCE TYPE → BOOSTING LOGIC
# ============================================================
def _doc_source_type(md: Dict[str, Any]) -> str:
    return (md.get("source_type") or md.get("content_type") or "").lower()


def _apply_source_boosts(md: Dict[str, Any], base_sim: float) -> float:
    st = _doc_source_type(md)
    sim = float(base_sim)

    # SharePoint (official guides, pdf, docx, faq)
    if st in ("sharepoint", "faq", "pdf", "docx", "doc", "table", "text"):
        sim *= SHAREPOINT_BOOST

        # extra boost for official manuals, guides, faqs
        content_type = (md.get("content_type") or "").lower()
        page_url = (md.get("page_url") or "").lower()
        if any(k in content_type for k in ["pdf", "doc", "docx", "guide", "manual", "faq", "table"]) or any(k in page_url for k in [".pdf", ".doc", ".docx"]):
            sim *= SHAREPOINT_DOC_EXTRA
            logger.info(f"[BOOST] SharePoint doc: {md.get('page_title') or md.get('source')}")

    # Web / blog / external articles
    elif st in ("web", "blog", "article") or md.get("is_blog_post"):
        sim *= WEB_NEUTRAL
        sim *= WEB_PENALTY   # keep blogs lower unless very relevant

    return sim


# ============================================================
# NORMALIZATION AND DEDUPLICATION
# ============================================================
def _normalize_candidates(candidates: List[Tuple[Any, float]]) -> List[Tuple[Any, float]]:
    """
    Deduplicate by (source + file_name + first 512 chars of content).
    Include file_name to prevent PDF/DOCX variants from being treated as duplicates.
    """
    seen = {}
    for doc, score in candidates:
        md = getattr(doc, "metadata", {}) or {}
        source = str(md.get("source", ""))
        file_name = str(md.get("file_name", "")) or str(md.get("page_title", "")) or str(md.get("post_title", ""))
        content_sample = (doc.page_content or "")[:512]
        key = f"{source}||{file_name}||{content_sample}"

        if key not in seen:
            seen[key] = (doc, score)
        else:
            _, existing_score = seen[key]
            if _as_similarity(score) > _as_similarity(existing_score):
                seen[key] = (doc, score)

    return list(seen.values())


# ============================================================
# CORE RERANKER
# ============================================================
def _compute_combined_score(semantic_sim: float, bm25: float, keyword_bonus: float) -> float:
    """
    Weighted combination:
    - semantic similarity: 0.55
    - BM25 score: 0.35
    - phrase/keyword bonus: 0.10
    """
    return (
        0.55 * semantic_sim +
        0.35 * bm25 +
        0.10 * keyword_bonus
    )


def rerank_with_metadata_and_ngrams(
    candidates: List[Tuple[Any, float]],
    query: str,
    detected_ngrams: List[str],
    ngram_weights: Dict[str, float]
) -> List[Tuple[Any, float]]:
    """
    Sorts by semantic similarity, BM25, phrase hits, and SharePoint priority.
    Output: list of (doc, final_similarity) sorted descending.
    """

    qnorm = normalize_text(query)
    phrase_norms = [normalize_text(p) for p in detected_ngrams]

    # collect scores for min-max normalization
    sem_raws = []
    bm_raws = []

    for doc, raw in candidates:
        sem_raws.append(_as_similarity(raw))
        bm_raws.append(float(getattr(doc, "_bm25_score", 0.0)))

    def minmax(x, arr):
        if not arr:
            return 0.0
        lo, hi = min(arr), max(arr)
        if hi - lo < 1e-9:
            return 0.0
        return (x - lo) / (hi - lo)

    scored = []

    for doc, raw in candidates:
        md = getattr(doc, "metadata", {}) or {}

        # normalize scores
        sem = minmax(_as_similarity(raw), sem_raws)
        bm25 = minmax(float(getattr(doc, "_bm25_score", 0.0)), bm_raws)

        # phrase hits
        content_low = (doc.page_content or "").lower()
        kb = 0.0
        phrase_hit = False

        page_title = normalize_text(md.get("page_title", "") or md.get("post_title", "") or md.get("source", ""))
        file_name = normalize_text(md.get("file_name", ""))

        for ph in phrase_norms:
            if ph and (ph in content_low or ph in page_title or ph in file_name):
                phrase_hit = True
                kb += ngram_weights.get(ph, 1.0)
                logger.info(f"[PHRASE HIT] {page_title or file_name or 'unnamed'} - matched: {ph}")

        # small token-level fallback
        for tok, wt in ngram_weights.items():
            if tok in content_low:
                kb += 0.1 * wt

        # boost for phrase hit
        base_sim = sem
        if phrase_hit:
            base_sim *= PHRASE_HIT_BOOST
            setattr(doc, "_phrase_hit", True)

            # extra boost when filename or page_title matches query tokens
            name_hits = sum(1 for w in qnorm.split() if len(w) > 3 and w in page_title)
            if name_hits >= 2:
                base_sim *= FILENAME_MATCH_BOOST
                logger.info(f"[FILENAME MATCH] {page_title or 'unnamed'} - {name_hits} terms matched")
        else:
            setattr(doc, "_phrase_hit", False)

        # metadata boosts (SharePoint > web/blog)
        base_sim = _apply_source_boosts(md, base_sim)

        # final score
        final = _compute_combined_score(base_sim, bm25, kb)
        scored.append((doc, final))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


# ============================================================
# MAIN HYBRID RETRIEVAL ENTRYPOINT
# ============================================================
def unified_retrieve(query: str, vectorstore, bm25_retriever=None, k: int = DEFAULT_K):
    print(f"\n{'='*70}")
    print(f"[UNIFIED RETRIEVAL] Query: {query}")
    print('='*70)
    
    logger.info(f"[UNIFIED] Query: {query}")

    detected_ngrams, ngram_weights = detect_technical_ngrams(query)
    logger.info(f"[UNIFIED] Detected phrases: {detected_ngrams}")
    print(f"[KEYWORDS] Detected: {detected_ngrams}")

    # CRITICAL: Check if vectorstore is available
    if vectorstore is None:
        print(f"[ERROR] Vectorstore not initialized - cannot perform retrieval")
        return []

    candidates = []

    # 1) Vector search
    try:
        if hasattr(vectorstore, "similarity_search_with_score"):
            vs = vectorstore.similarity_search_with_score(query, k=max(k, 100))
            candidates.extend(vs)
            print(f"[VECTOR] Retrieved {len(vs)} documents with scores")
        else:
            vs = vectorstore.similarity_search(query, k=max(k, 100))
            candidates.extend([(doc, 0.0) for doc in vs])
            print(f"[VECTOR] Retrieved {len(vs)} documents (no scores)")
    except Exception as e:
        logger.warning(f"[UNIFIED] Vector search failed: {e}")
        print(f"[VECTOR] Error: {e}")
    
    # 2) BM25 retrieval
    if bm25_retriever:
        try:
            bm_docs = bm25_retriever.get_relevant_documents(query)
            for i, doc in enumerate(bm_docs):
                setattr(doc, "_bm25_score", float(len(bm_docs) - i))
            candidates.extend([(doc, 0.0) for doc in bm_docs])
            print(f"[BM25] Retrieved {len(bm_docs)} documents")
            logger.info(f"[UNIFIED] BM25 retrieved {len(bm_docs)} docs")
        except Exception as e:
            logger.warning(f"[UNIFIED] BM25 failed: {e}")
            print(f"[BM25] Error: {e}")
    else:
        # Fallback: Try to use BM25 from endpoints if available
        try:
            from app.endpoints import bm25_search
            bm25_results = bm25_search(query, k=k)
            if bm25_results:
                candidates.extend(bm25_results)
                print(f"[BM25] Retrieved {len(bm25_results)} documents from endpoints")
        except Exception as e:
            print(f"[BM25] Not available: {e}")
    
    if not candidates:
        print("[WARNING] No documents retrieved!")
        return []
    
    # 3) Dedupe
    candidates = _normalize_candidates(candidates)
    logger.info(f"[UNIFIED] Candidates after dedupe: {len(candidates)}")
    print(f"[DEDUP] Normalized to {len(candidates)} unique documents")

    # 4) Rerank
    reranked = rerank_with_metadata_and_ngrams(candidates, query, detected_ngrams, ngram_weights)

    # 5) Debug logging
    top_titles = []
    sharepoint_in_top10 = []
    for d, s in reranked[:10]:
        md = getattr(d, "metadata", {}) or {}
        title = md.get("page_title") or md.get("post_title") or md.get("source") or "unnamed"
        top_titles.append((title, round(s, 4)))
        if _doc_source_type(md) in ("sharepoint", "doc", "pdf", "faq"):
            sharepoint_in_top10.append(title)
    
    logger.info(f"[UNIFIED] Top docs (first 10): {top_titles}")
    print(f"[TOP 3 SCORES] {[f'{s:.3f}' for _, s in reranked[:3]]}")
    if sharepoint_in_top10:
        print(f"[TOP 10 SHAREPOINT] {sharepoint_in_top10}")

    print(f"[FINAL] Returning top {min(len(reranked), MAX_RETURN)} documents")
    print('='*70)
    
    # 6) Return top-N results
    return reranked[:min(len(reranked), MAX_RETURN)]


# ============================================================
# LEGACY EXPORTS (for backward compatibility)
# ============================================================
def extract_query_keywords(query: str, min_length: int = 3) -> List[str]:
    """Extract keywords from query (legacy function)."""
    detected_ngrams, _ = detect_technical_ngrams(query)
    return detected_ngrams


def create_unified_prompt(context_docs: List, query: str) -> str:
    """
    Create unified prompt that works for all query types (legacy function).
    """
    formatted_context = []
    
    for i, doc in enumerate(context_docs, 1):
        content = doc.page_content
        metadata = doc.metadata
        
        # Add source attribution
        source = metadata.get('source', 'Unknown')
        tag = metadata.get('tag', 'general')
        
        # Format based on content type
        if metadata.get('source_type') == 'sharepoint':
            page_title = metadata.get('page_title', '')
            formatted_context.append(f"[Document {i} - {tag} - {page_title}]\n{content}")
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


def get_unified_retriever(vectorstore, bm25_retriever=None):
    """Get retriever function for use in endpoints (legacy function)."""
    def retriever(query: str, k: int = DEFAULT_K):
        return unified_retrieve(query, vectorstore, bm25_retriever, k)
    return retriever
