"""
N-gram Feature Extraction for Technical Query Retrieval
========================================================

This module implements N-gram extraction and boosting to improve retrieval
accuracy for technical queries. It addresses the problem where short technical
terms (like "JSON", "API") are not given enough weight in pure semantic search.

Key features:
1. Extract bigrams and trigrams from queries
2. Detect technical phrases (e.g., "json migration", "api access")
3. Boost documents containing these phrases
4. Filter and prioritize technical documentation
"""

from typing import List, Tuple, Dict, Any
import re
from nltk import ngrams
from nltk.tokenize import word_tokenize
import nltk

# Safe tokenization fallback
def safe_tokenize(text: str) -> List[str]:
    """Safe tokenization with fallback if NLTK fails."""
    try:
        return word_tokenize(text.lower())
    except Exception:
        # Fallback to simple regex tokenization
        return re.findall(r"\w+", text.lower())

# Download required NLTK data (only once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("[NLTK] Downloading punkt tokenizer...")
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    print("[NLTK] Downloading punkt_tab tokenizer...")
    nltk.download('punkt_tab', quiet=True)

# ============================================================================
# TECHNICAL PHRASE TAXONOMY
# ============================================================================

# Technical Unigrams (single words) that should receive boost weights
TECHNICAL_UNIGRAMS = {
    # Core brand and product terms
    "cloudfuze": 2.5,
    "json": 2.3,
    "api": 2.2,
    "metadata": 2.4,
    "permissions": 2.3,
    "sharepoint": 2.4,
    "onedrive": 2.4,
    "teams": 2.2,
    "slack": 2.2,
    "migration": 2.3,
    
    # Security and compliance
    "compliance": 2.2,
    "encryption": 2.3,
    "authentication": 2.2,
    "authorization": 2.2,
    "oauth": 2.3,
    "ssl": 2.2,
    "tls": 2.2,
    "gdpr": 2.3,
    "hipaa": 2.3,
    "soc": 2.3,
    
    # Technical terms
    "endpoint": 2.1,
    "webhook": 2.2,
    "token": 2.1,
    "schema": 2.2,
    "batch": 2.1,
    "incremental": 2.2,
    "delta": 2.2,
    "throughput": 2.1,
    "bandwidth": 2.1,
    
    # Data and file operations
    "export": 2.0,
    "import": 2.0,
    "sync": 2.1,
    "backup": 2.0,
    "restore": 2.0,
    "archive": 2.0,
    
    # Metadata attributes (important for "created by" type queries)
    "created": 2.2,
    "modified": 2.2,
    "owner": 2.2,
    "author": 2.2,
    "timestamp": 2.1,
    "versioning": 2.1,
}

# Technical N-grams that should receive high boost weights
TECHNICAL_BIGRAMS = {
    # Migration-specific technical phrases
    "json migration": 3.0,
    "api access": 2.8,
    "api migration": 2.8,
    "metadata mapping": 2.7,
    "schema validation": 2.7,
    "token refresh": 2.5,
    "oauth authentication": 2.6,
    "rate limiting": 2.5,
    "batch processing": 2.5,
    "delta migration": 2.7,
    "incremental migration": 2.7,
    
    # Slack to Teams specific
    "slack teams": 2.8,
    "teams migration": 2.7,
    "slack migration": 2.7,
    "channel migration": 2.6,
    "workspace migration": 2.6,
    "conversation history": 2.5,
    "slack channels": 2.5,
    "teams channels": 2.5,
    "direct messages": 2.4,
    "private channels": 2.4,
    "shared channels": 2.4,
    
    # Technical implementation
    "migration logs": 2.6,
    "error handling": 2.5,
    "api endpoint": 2.6,
    "api endpoints": 2.6,
    "rest api": 2.6,
    "api documentation": 2.7,
    "api key": 2.4,
    "api keys": 2.4,
    "access token": 2.4,
    "access tokens": 2.4,
    
    # Data management
    "data transfer": 2.5,
    "file transfer": 2.5,
    "permission mapping": 2.6,
    "user mapping": 2.6,
    "folder structure": 2.4,
    "folder hierarchy": 2.4,
    
    # Performance and limits
    "migration speed": 2.5,
    "transfer rate": 2.5,
    "daily limit": 2.4,
    "rate limit": 2.5,
    "throughput limit": 2.5,
    "concurrent transfers": 2.5,
    
    # SharePoint and OneDrive
    "sharepoint migration": 2.7,
    "onedrive migration": 2.7,
    "sharepoint online": 2.6,
    "document library": 2.5,
    "site collection": 2.5,
    
    # Security and compliance
    "security compliance": 2.6,
    "data encryption": 2.6,
    "audit logs": 2.5,
    "compliance certification": 2.6,
    "soc certification": 2.7,
    "gdpr compliance": 2.6,
    
    # Technical architecture
    "cloud architecture": 2.5,
    "api integration": 2.6,
    "webhook integration": 2.5,
    "authentication flow": 2.5,
    "authorization flow": 2.5,
}

TECHNICAL_TRIGRAMS = {
    # Three-word technical phrases
    "slack to teams": 3.0,
    "json slack migration": 3.0,
    "json teams migration": 3.0,
    "api rate limiting": 2.7,
    "oauth authentication flow": 2.7,
    "metadata schema mapping": 2.8,
    "incremental delta migration": 2.8,
    "channel conversation history": 2.6,
    "rest api endpoint": 2.7,
    "api access token": 2.6,
    "migration audit logs": 2.7,
    "user permission mapping": 2.7,
    "sharepoint document library": 2.6,
    "onedrive folder structure": 2.6,
    "security compliance certification": 2.7,
}

# Document type priorities based on N-gram detection
DOC_TYPE_BOOSTS = {
    "technical_doc": 1.8,
    "implementation_guide": 1.7,
    "api_documentation": 1.9,
    "architecture_doc": 1.6,
    "migration_guide": 1.7,
    "troubleshooting_guide": 1.6,
}

# Metadata tags that indicate technical documentation
TECHNICAL_TAGS = [
    "api",
    "technical",
    "implementation",
    "architecture",
    "developer",
    "integration",
    "schema",
    "metadata",
    "authentication",
    "migration-technical",
]


# ============================================================================
# N-GRAM EXTRACTION
# ============================================================================

def extract_ngrams(query: str, n: int = 2) -> List[str]:
    """
    Extract n-grams (bigrams, trigrams) from a query.
    
    Args:
        query: User query string
        n: N-gram size (2 for bigrams, 3 for trigrams)
    
    Returns:
        List of n-gram strings
    
    Example:
        >>> extract_ngrams("how does JSON Slack to Teams migration work", n=2)
        ['how does', 'does json', 'json slack', 'slack to', 'to teams', 
         'teams migration', 'migration work']
    """
    # Tokenize and normalize using safe tokenizer
    tokens = safe_tokenize(query)
    
    # Remove punctuation and very short tokens
    tokens = [t for t in tokens if len(t) > 1 and t.isalnum()]
    
    # Generate n-grams
    if len(tokens) < n:
        return []
    
    ngram_list = list(ngrams(tokens, n))
    ngram_strings = [' '.join(gram) for gram in ngram_list]
    
    return ngram_strings


def extract_all_ngrams(query: str) -> Dict[str, List[str]]:
    """
    Extract both bigrams and trigrams from a query.
    
    Args:
        query: User query string
    
    Returns:
        Dictionary with 'bigrams' and 'trigrams' keys
    """
    return {
        'bigrams': extract_ngrams(query, n=2),
        'trigrams': extract_ngrams(query, n=3),
    }


# ============================================================================
# TECHNICAL PHRASE DETECTION
# ============================================================================

def detect_technical_ngrams(query: str) -> Tuple[List[str], Dict[str, float]]:
    """
    Detect technical n-grams (unigrams, bigrams, trigrams) in a query and return them with their boost weights.
    
    Args:
        query: User query string
    
    Returns:
        Tuple of (detected_ngrams, ngram_weights)
        - detected_ngrams: List of technical n-grams found (includes single words and phrases)
        - ngram_weights: Dict mapping n-gram to its boost weight
    
    Example:
        >>> detect_technical_ngrams("how does JSON Slack to Teams migration work")
        (['json', 'slack', 'teams', 'migration', 'slack to teams'], 
         {'json': 2.3, 'slack': 2.2, 'teams': 2.2, 'migration': 2.3, 'slack to teams': 3.0})
    """
    query_lower = query.lower()
    all_ngrams = extract_all_ngrams(query)
    
    detected_ngrams = []
    ngram_weights = {}
    
    # Check trigrams first (most specific)
    for trigram in all_ngrams['trigrams']:
        if trigram in TECHNICAL_TRIGRAMS:
            detected_ngrams.append(trigram)
            ngram_weights[trigram] = TECHNICAL_TRIGRAMS[trigram]
    
    # Check bigrams
    for bigram in all_ngrams['bigrams']:
        if bigram in TECHNICAL_BIGRAMS:
            detected_ngrams.append(bigram)
            ngram_weights[bigram] = TECHNICAL_BIGRAMS[bigram]
    
    # Check unigrams (single words) - NEW!
    # Tokenize the query to extract individual words
    tokens = safe_tokenize(query_lower)
    # Remove short tokens and punctuation
    tokens = [t for t in tokens if len(t) > 2 and t.isalnum()]
    
    for token in tokens:
        if token in TECHNICAL_UNIGRAMS:
            # Avoid duplicates
            if token not in ngram_weights:
                detected_ngrams.append(token)
                ngram_weights[token] = TECHNICAL_UNIGRAMS[token]
    
    return detected_ngrams, ngram_weights


def is_technical_query(query: str, threshold: int = 1) -> bool:
    """
    Determine if a query is technical based on n-gram detection.
    
    Args:
        query: User query string
        threshold: Minimum number of technical n-grams to classify as technical
    
    Returns:
        True if query contains >= threshold technical n-grams
    """
    detected_ngrams, _ = detect_technical_ngrams(query)
    return len(detected_ngrams) >= threshold


def get_query_technical_score(query: str) -> float:
    """
    Calculate a technical score for a query based on detected n-grams.
    
    Args:
        query: User query string
    
    Returns:
        Technical score (sum of all detected n-gram weights)
    
    Example:
        >>> get_query_technical_score("how does JSON Slack migration work")
        5.5  # json slack (2.8) + slack migration (2.7)
    """
    _, ngram_weights = detect_technical_ngrams(query)
    return sum(ngram_weights.values())


# ============================================================================
# DOCUMENT SCORING AND BOOSTING
# ============================================================================

def score_document_for_ngrams(
    doc_content: str,
    doc_metadata: Dict[str, Any],
    detected_ngrams: List[str],
    ngram_weights: Dict[str, float]
) -> float:
    """
    Score a document based on how many technical n-grams it contains.
    
    Args:
        doc_content: Document content (page_content)
        doc_metadata: Document metadata
        detected_ngrams: List of technical n-grams from query
        ngram_weights: Dict mapping n-gram to boost weight
    
    Returns:
        Boost score for this document
    """
    doc_content_lower = doc_content.lower()
    doc_metadata_str = str(doc_metadata).lower()
    
    boost_score = 0.0
    
    # Check each detected n-gram
    for ngram in detected_ngrams:
        ngram_weight = ngram_weights.get(ngram, 1.0)
        
        # Count occurrences in content (capped at 3 to avoid over-boosting repetitive docs)
        content_count = min(doc_content_lower.count(ngram), 3)
        
        # Check metadata for n-gram (tags, source, etc.)
        metadata_match = 1.0 if ngram in doc_metadata_str else 0.0
        
        # Calculate boost for this n-gram
        ngram_boost = (content_count * ngram_weight) + (metadata_match * ngram_weight * 0.5)
        boost_score += ngram_boost
    
    # Additional boost for technical document types (additive, not multiplicative)
    boost_bonus = 0.0
    doc_type = doc_metadata.get('doc_type', '')
    if doc_type in DOC_TYPE_BOOSTS:
        # Convert multiplicative boost to additive bonus
        boost_bonus += (DOC_TYPE_BOOSTS[doc_type] - 1.0) * 0.5
    
    # Additional boost for technical tags (smaller additive bonus)
    doc_tags = doc_metadata.get('tags', [])
    if isinstance(doc_tags, list):
        for tag in doc_tags:
            if tag.lower() in TECHNICAL_TAGS:
                boost_bonus += 0.15
                break
    
    # Additional boost for SharePoint technical documentation
    source_type = doc_metadata.get('source_type', '')
    tag = doc_metadata.get('tag', '')
    if source_type == 'sharepoint' and any(tech_term in tag.lower() for tech_term in ['technical', 'api', 'developer', 'implementation']):
        boost_bonus += 0.20
    
    # Apply additive bonus
    boost_score = boost_score + boost_bonus
    
    return boost_score


def rerank_documents_with_ngrams(
    documents: List[Any],
    query: str,
    base_relevance_scores: List[float] = None
) -> List[Tuple[Any, float]]:
    """
    Re-rank documents based on n-gram matching and technical relevance.
    
    Args:
        documents: List of Document objects from vector search
        query: User query string
        base_relevance_scores: Optional list of base similarity scores from vector search
    
    Returns:
        List of (document, combined_score) tuples, sorted by score (descending)
    """
    # Detect technical n-grams in query
    detected_ngrams, ngram_weights = detect_technical_ngrams(query)
    
    if not detected_ngrams:
        # No technical n-grams detected, return documents with original scores
        if base_relevance_scores:
            return list(zip(documents, base_relevance_scores))
        else:
            return [(doc, 1.0) for doc in documents]
    
    # Score each document
    scored_docs = []
    for i, doc in enumerate(documents):
        # Get base score (semantic similarity from vector search)
        # Assume base_score is in [0,1] range (cosine similarity)
        base_score = base_relevance_scores[i] if base_relevance_scores else 1.0
        
        # Calculate n-gram boost score
        ngram_score = score_document_for_ngrams(
            doc.page_content,
            doc.metadata,
            detected_ngrams,
            ngram_weights
        )
        
        # Cap ngram_score to prevent dominance
        ngram_score_capped = min(ngram_score, 5.0)
        
        # Normalize ngram score to [0,1] range
        ngram_norm = ngram_score_capped / 5.0
        
        # Weighted hybrid combination (70% semantic, 30% n-gram)
        # This prevents n-gram from dominating and maintains semantic relevance
        combined_score = (0.7 * base_score) + (0.3 * ngram_norm)
        
        scored_docs.append((doc, combined_score))
    
    # Sort by combined score (descending)
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    return scored_docs


# ============================================================================
# QUERY EXPANSION FOR TECHNICAL QUERIES
# ============================================================================

def expand_technical_query(query: str) -> List[str]:
    """
    Expand a technical query with related terms and phrases.
    
    Args:
        query: User query string
    
    Returns:
        List of expanded query variations
    """
    detected_ngrams, _ = detect_technical_ngrams(query)
    
    if not detected_ngrams:
        return [query]
    
    expansions = [query]  # Always include original
    
    # Add expansions based on detected technical phrases
    query_lower = query.lower()
    
    # Slack to Teams expansions
    if any(ng in detected_ngrams for ng in ['slack teams', 'slack to teams', 'teams migration']):
        expansions.extend([
            query + " channel migration",
            query + " conversation history",
            query + " workspace transfer",
        ])
    
    # JSON migration expansions
    if 'json migration' in detected_ngrams or 'json slack' in detected_ngrams:
        expansions.extend([
            query + " data format",
            query + " export import process",
            query + " JSON schema",
        ])
    
    # API access expansions
    if 'api access' in detected_ngrams or 'api endpoint' in detected_ngrams:
        expansions.extend([
            query + " authentication",
            query + " REST API",
            query + " API documentation",
        ])
    
    # Metadata mapping expansions
    if 'metadata mapping' in detected_ngrams:
        expansions.extend([
            query + " field mapping",
            query + " schema transformation",
            query + " data mapping",
        ])
    
    return expansions[:5]  # Limit to 5 expansions


# ============================================================================
# LOGGING AND DIAGNOSTICS
# ============================================================================

def get_ngram_diagnostics(query: str) -> Dict[str, Any]:
    """
    Get diagnostic information about n-gram detection for a query.
    Useful for debugging and Langfuse logging.
    
    Args:
        query: User query string
    
    Returns:
        Dictionary with diagnostic information
    """
    all_ngrams = extract_all_ngrams(query)
    detected_ngrams, ngram_weights = detect_technical_ngrams(query)
    technical_score = get_query_technical_score(query)
    is_tech = is_technical_query(query)
    
    return {
        'query': query,
        'all_bigrams': all_ngrams['bigrams'],
        'all_trigrams': all_ngrams['trigrams'],
        'detected_technical_ngrams': detected_ngrams,
        'ngram_weights': ngram_weights,
        'technical_score': technical_score,
        'is_technical_query': is_tech,
        'query_expansions': expand_technical_query(query),
    }


if __name__ == "__main__":
    # Test examples
    test_queries = [
        "how does JSON Slack to Teams migration work",
        "what API access does CloudFuze support",
        "are migration logs available for OneDrive transfers",
        "general information about CloudFuze",
    ]
    
    print("N-gram Extraction Test\n" + "="*60)
    for query in test_queries:
        print(f"\nQuery: {query}")
        diagnostics = get_ngram_diagnostics(query)
        print(f"  Technical N-grams: {diagnostics['detected_technical_ngrams']}")
        print(f"  Weights: {diagnostics['ngram_weights']}")
        print(f"  Technical Score: {diagnostics['technical_score']:.2f}")
        print(f"  Is Technical: {diagnostics['is_technical_query']}")

