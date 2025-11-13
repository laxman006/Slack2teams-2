# -*- coding: utf-8 -*-
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import httpx
import os
import json
import asyncio
import re
from datetime import datetime

from app.llm import setup_qa_chain
from app.vectorstore import retriever, vectorstore
from app.mongodb_memory import add_to_conversation, get_conversation_context, get_user_chat_history, clear_user_chat_history
from app.helpers import preserve_markdown, normalize_chain_output
from app.langfuse_integration import langfuse_tracker
from app.auth import verify_user_access, require_admin, require_auth
from app.prompt_manager import get_system_prompt, compile_prompt
from config import SYSTEM_PROMPT, MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_TENANT
from langchain_core.prompts import ChatPromptTemplate
import time
from sentence_transformers import SentenceTransformer, util


# ============================================================================
# CONTEXT RELEVANCE DETECTION - Semantic Similarity & Topic Gating
# ============================================================================

# Initialize sentence transformer model once (global)
try:
    SIMILARITY_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    print("[OK] Sentence transformer model loaded for context relevance detection")
except Exception as e:
    print(f"[WARNING] Failed to load sentence transformer model: {e}")
    SIMILARITY_MODEL = None

# Topic taxonomy for all migration types and services
MIGRATION_TOPICS = {
    'google_workspace': ['google', 'workspace', 'gdrive', 'gmail', 'shared drives', 'google drive'],
    'dropbox_onedrive': ['dropbox', 'onedrive', 'microsoft onedrive'],
    'slack_teams': ['slack', 'teams', 'microsoft teams', 'channels', 'slack channels'],
    'box': ['box', 'box storage', 'box cloud'],
    'sharepoint': ['sharepoint', 'sharepoint online'],
    's3': ['s3', 'amazon s3', 'aws s3'],
    'azure': ['azure', 'azure blob'],
    'general': ['security', 'gdpr', 'compliance', 'pricing', 'cost', 'api', 'enterprise']
}

# Ambiguous terms that could apply to multiple platforms
AMBIGUOUS_TERMS = {
    'shared drives': ['google_workspace', 'dropbox_onedrive'],
    'permissions': ['google_workspace', 'dropbox_onedrive', 'slack_teams', 'box', 'sharepoint'],
    'folders': ['google_workspace', 'dropbox_onedrive', 'box', 'sharepoint'],
    'channels': ['slack_teams'],
    'files': ['google_workspace', 'dropbox_onedrive', 'box', 'sharepoint'],
    'migration': ['google_workspace', 'dropbox_onedrive', 'slack_teams', 'box', 'sharepoint']
}


def semantic_similarity_check(new_query: str, previous_query: str, threshold: float = 0.65) -> bool:
    """
    Check semantic similarity between two queries using sentence transformers.
    Returns True if similarity >= threshold, indicating related queries.
    
    Args:
        new_query: Current user question
        previous_query: Previous user question
        threshold: Similarity threshold (0.6-0.7 works well for topic detection)
    
    Returns:
        bool: True if queries are semantically similar
    """
    if not previous_query or not new_query or SIMILARITY_MODEL is None:
        return False
    
    try:
        # Encode both queries
        emb_new = SIMILARITY_MODEL.encode(new_query, convert_to_tensor=True)
        emb_prev = SIMILARITY_MODEL.encode(previous_query, convert_to_tensor=True)
        
        # Calculate cosine similarity
        similarity = util.cos_sim(emb_new, emb_prev).item()
        
        print(f"[SEMANTIC SIMILARITY] Score: {similarity:.3f} (threshold: {threshold})")
        return similarity >= threshold
        
    except Exception as e:
        print(f"[ERROR] Semantic similarity check failed: {e}")
        return False


def detect_query_topic(query: str) -> str:
    """
    Detect which migration topic/platform the query relates to.
    
    Args:
        query: User question
    
    Returns:
        str: Topic key (e.g., 'google_workspace', 'slack_teams', 'general')
    """
    query_lower = query.lower()
    
    # Check each topic's keywords
    for topic, keywords in MIGRATION_TOPICS.items():
        if any(keyword in query_lower for keyword in keywords):
            return topic
    
    return 'general'


def needs_clarification(query: str, previous_topic: str = None) -> tuple:
    """
    Check if query uses ambiguous terms that could apply to multiple platforms.
    
    Args:
        query: User question
        previous_topic: Previously discussed topic (if any)
    
    Returns:
        tuple: (needs_clarification: bool, ambiguous_term: str, applicable_topics: list)
    """
    query_lower = query.lower()
    
    for term, applicable_topics in AMBIGUOUS_TERMS.items():
        if term in query_lower:
            # If previous topic is one of the applicable ones, no clarification needed
            if previous_topic and previous_topic in applicable_topics:
                return False, None, None
            
            # If query explicitly mentions one of the platforms, no clarification needed
            detected_topic = detect_query_topic(query)
            if detected_topic in applicable_topics:
                return False, None, None
            
            # Otherwise, need clarification
            return True, term, applicable_topics
    
    return False, None, None








# ============================================================================
# TRUE HYBRID SEARCH - BM25 + Vector + Reciprocal Rank Fusion (RRF)
# ============================================================================

# Global BM25 index (built once, reused)
_BM25_INDEX = None
_BM25_DOCS = None
_BM25_LAST_BUILD = None

def build_bm25_index():
    """Build BM25 index from all documents in vectorstore. Cached for reuse."""
    global _BM25_INDEX, _BM25_DOCS, _BM25_LAST_BUILD
    
    # Check if we need to rebuild (cache for 1 hour)
    import time
    current_time = time.time()
    if _BM25_INDEX is not None and _BM25_LAST_BUILD is not None:
        if current_time - _BM25_LAST_BUILD < 3600:  # 1 hour cache
            return _BM25_INDEX, _BM25_DOCS
    
    if vectorstore is None:
        print("[WARNING] Cannot build BM25 index: vectorstore not available")
        return None, None
    
    try:
        from rank_bm25 import BM25Okapi
        import time as time_module
        
        start_time = time_module.time()
        print("[BM25] Building BM25 index from vectorstore...")
        
        # Get all documents from vectorstore
        collection = vectorstore._collection
        all_data = collection.get(include=['documents', 'metadatas'])
        
        _BM25_DOCS = []
        tokenized_corpus = []
        
        for i, (doc_text, metadata) in enumerate(zip(all_data['documents'], all_data['metadatas'])):
            # Store document with metadata for retrieval
            from langchain_core.documents import Document
            doc_obj = Document(page_content=doc_text, metadata=metadata)
            _BM25_DOCS.append(doc_obj)
            
            # Tokenize for BM25 (simple word splitting)
            tokens = doc_text.lower().split()
            tokenized_corpus.append(tokens)
        
        # Build BM25 index
        _BM25_INDEX = BM25Okapi(tokenized_corpus)
        _BM25_LAST_BUILD = current_time
        
        elapsed = time_module.time() - start_time
        print(f"[BM25] ✓ Built BM25 index with {len(_BM25_DOCS)} documents in {elapsed:.2f}s")
        
        return _BM25_INDEX, _BM25_DOCS
        
    except Exception as e:
        print(f"[BM25] ERROR building index: {e}")
        return None, None


def bm25_search(query: str, k: int = 50):
    """Perform BM25 keyword search."""
    bm25_index, bm25_docs = build_bm25_index()
    
    if bm25_index is None or bm25_docs is None:
        return []
    
    try:
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = bm25_index.get_scores(query_tokens)
        
        # Get top k document indices
        import numpy as np
        top_indices = np.argsort(scores)[::-1][:k]
        
        # Return documents with scores
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include docs with non-zero score
                results.append((bm25_docs[idx], float(scores[idx])))
        
        print(f"[BM25] Found {len(results)} results with scores > 0")
        return results
        
    except Exception as e:
        print(f"[BM25] ERROR during search: {e}")
        return []


def reciprocal_rank_fusion(vector_results, bm25_results, k=60):
    """
    Merge vector and BM25 results using Reciprocal Rank Fusion (RRF).
    
    RRF formula: score(doc) = sum(1 / (k + rank_i)) for all rankings where doc appears
    
    Args:
        vector_results: List of (Document, score) tuples from vector search
        bm25_results: List of (Document, score) tuples from BM25
        k: Constant for RRF (typically 60)
    
    Returns:
        List of (Document, rrf_score) tuples, sorted by RRF score (descending)
    """
    from collections import defaultdict
    
    # Track RRF scores for each document
    rrf_scores = defaultdict(float)
    doc_objects = {}  # Map doc_id to Document object
    
    # Process vector search results (rank 1 is best)
    for rank, (doc, score) in enumerate(vector_results, start=1):
        doc_id = id(doc)  # Use object id as unique identifier
        doc_objects[doc_id] = doc
        rrf_scores[doc_id] += 1.0 / (k + rank)
    
    # Process BM25 results (rank 1 is best)
    for rank, (doc, score) in enumerate(bm25_results, start=1):
        doc_id = id(doc)
        if doc_id not in doc_objects:
            doc_objects[doc_id] = doc
        rrf_scores[doc_id] += 1.0 / (k + rank)
    
    # Sort by RRF score (descending)
    sorted_results = sorted(
        [(doc_objects[doc_id], score) for doc_id, score in rrf_scores.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    print(f"[RRF] Merged {len(vector_results)} vector + {len(bm25_results)} BM25 results → {len(sorted_results)} unique documents")
    
    return sorted_results


def hybrid_retrieve(query: str, k: int = 50):
    """
    TRUE HYBRID SEARCH: Combines BM25 keyword search + Vector semantic search.
    Uses Reciprocal Rank Fusion (RRF) to merge results.
    
    This is the industry best practice for enterprise RAG systems.
    """
    # 1. Vector search (semantic)
    if vectorstore is not None:
        vector_results = vectorstore.similarity_search_with_score(query, k=k)
        print(f"[HYBRID] Vector search: {len(vector_results)} results")
    else:
        vector_results = []
        print(f"[HYBRID] No vectorstore available")
    
    # 2. BM25 search (keyword)
    bm25_results = bm25_search(query, k=k)
    print(f"[HYBRID] BM25 search: {len(bm25_results)} results")
    
    # 3. Merge with Reciprocal Rank Fusion
    if len(vector_results) == 0 and len(bm25_results) == 0:
        print(f"[HYBRID] No results from either search method")
        return []
    elif len(vector_results) == 0:
        print(f"[HYBRID] Using BM25 results only")
        return bm25_results
    elif len(bm25_results) == 0:
        print(f"[HYBRID] Using vector results only")
        return vector_results
    else:
        # True hybrid: merge both
        merged_results = reciprocal_rank_fusion(vector_results, bm25_results, k=60)
        print(f"[HYBRID] ✓ Merged results using RRF: {len(merged_results)} documents")
        return merged_results









def calculate_document_diversity(doc_results):
    """
    Calculate diversity score for retrieved documents.
    Higher diversity = more varied sources and topics.
    """
    sources = set()
    tags = set()
    titles = set()
    
    for doc, score in doc_results[:30]:  # Check top 30
        source_type = doc.metadata.get('source_type', 'unknown')
        tag = doc.metadata.get('tag', 'unknown')
        title = doc.metadata.get('post_title', doc.metadata.get('file_name', ''))
        
        sources.add(source_type)
        tags.add(tag)
        if title:
            titles.add(title[:50])  # First 50 chars to avoid duplicates
    
    # Diversity metrics
    source_diversity = len(sources) / max(len(doc_results[:30]), 1)
    tag_diversity = len(tags) / max(len(doc_results[:30]), 1)
    title_diversity = len(titles) / max(len(doc_results[:30]), 1)
    
    # Overall diversity score (0-1)
    overall_diversity = (source_diversity + tag_diversity + title_diversity) / 3
    
    return {
        "overall": round(overall_diversity, 3),
        "source_diversity": round(source_diversity, 3),
        "tag_diversity": round(tag_diversity, 3),
        "title_diversity": round(title_diversity, 3),
        "unique_sources": len(sources),
        "unique_tags": len(tags),
        "unique_titles": len(titles)
    }




router = APIRouter()

qa_chain = setup_qa_chain(retriever)


# File path for corrected responses
CORRECTED_RESPONSES_FILE = "./data/corrected_responses/corrected_responses.json"

def load_corrected_responses():
    """Load corrected responses from JSON file."""
    try:
        if os.path.exists(CORRECTED_RESPONSES_FILE):
            with open(CORRECTED_RESPONSES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('corrected_responses', [])
    except Exception as e:
        print(f"Error loading corrected responses: {e}")
    return []

def find_similar_corrected_response(question: str, threshold: float = 0.7):
    """Check if there's a corrected response for a similar question."""
    from difflib import SequenceMatcher
    
    corrected_responses = load_corrected_responses()
    
    if not corrected_responses:
        return None
    
    # Match against corrected responses directly
    # The feedback_history.json has a nested structure with trace_ids as keys
    try:
        best_match = None
        best_score = 0
        
        # Iterate through corrected responses to find matches
        for corrected in corrected_responses:
            # Get the original question if stored in corrected response
            original_question = corrected.get('original_question', '')
            
            if original_question:
                # Calculate similarity
                similarity = SequenceMatcher(None, question.lower(), original_question.lower()).ratio()
                
                if similarity > best_score and similarity >= threshold:
                    best_score = similarity
                    best_match = {
                        'response': corrected.get('corrected_response'),
                        'similarity': similarity,
                        'original_question': original_question
                    }
        
        if best_match:
            print(f"[OK] Found corrected response (similarity: {best_match['similarity']:.2%})")
            print(f"    Original question: {best_match['original_question']}")
            return best_match['response']
                
    except Exception as e:
        print(f"[WARNING] Error checking corrected responses: {e}")
    
    return None

def classify_query_type(question: str) -> str:
    """Classify query as informational, conversational, or transactional."""
    question_lower = question.lower()
    
    # Conversational indicators
    conversational_patterns = ["how are you", "who are you", "what are you", "your name", "thank you", "thanks", "hi", "hello", "bye"]
    if any(pattern in question_lower for pattern in conversational_patterns):
        return "conversational"
    
    # Transactional indicators
    transactional_patterns = ["download", "buy", "purchase", "subscribe", "sign up", "register", "login"]
    if any(pattern in question_lower for pattern in transactional_patterns):
        return "transactional"
    
    return "informational"

def classify_query_category(question: str) -> str:
    """Classify query into categories like migration, pricing, technical, etc."""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ["price", "cost", "pricing", "fee", "payment", "subscription"]):
        return "pricing"
    elif any(word in question_lower for word in ["migrate", "migration", "transfer", "move data"]):
        return "migration"
    elif any(word in question_lower for word in ["error", "issue", "problem", "not working", "troubleshoot", "fix"]):
        return "support"
    elif any(word in question_lower for word in ["how to", "tutorial", "guide", "steps", "instructions"]):
        return "how_to"
    elif any(word in question_lower for word in ["certificate", "ssl", "security", "authentication", "oauth"]):
        return "security"
    elif any(word in question_lower for word in ["sharepoint", "onedrive", "google drive", "dropbox", "box"]):
        return "platform_specific"
    elif any(word in question_lower for word in ["api", "integration", "webhook", "developer"]):
        return "technical"
    else:
        return "general"


def get_vectorstore_build_date() -> str:
    """Get the actual vectorstore build date from metadata file."""
    try:
        with open('./data/vectorstore_metadata.json', 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            timestamp = metadata.get('timestamp', '')
            # Convert "2025-11-01T17:27:05.640130" to "2025-11-01"
            return timestamp.split('T')[0] if timestamp else "unknown"
    except FileNotFoundError:
        return "unknown"
    except Exception as e:
        print(f"[WARNING] Failed to read vectorstore metadata: {e}")
        return "unknown"

def is_conversational_query(question: str) -> bool:
    """Determine if a query is conversational/social rather than informational."""
    question_lower = question.lower().strip()
    
    # Common conversational patterns
    conversational_patterns = [
        r'^(hi|hello|hey|hiya|howdy)',
        r'^(how are you|how\'re you|how do you do)',
        r'^(what\'s up|whats up|wassup)',
        r'^(good morning|good afternoon|good evening)',
        r'^(thanks|thank you|thx)',
        r'^(bye|goodbye|see you|farewell)',
        r'^(yes|no|ok|okay|sure|alright)',
        r'^(what|who|where|when|why|how)\s+(are you|is it|was it)',
        r'^(tell me about yourself|who are you)',
        r'^(what can you do|what do you do)',
        r'^(help|can you help)',
        r'^(sorry|excuse me|pardon)',
        r'^(nice|good|great|awesome|cool|wow)',
        r'^(please|pls)',
    ]
    
    # Check if question matches conversational patterns
    for pattern in conversational_patterns:
        if re.match(pattern, question_lower):
            return True
    
    # Check for very short queries (likely conversational)
    if len(question.strip()) < 10 and not any(word in question_lower for word in ['what', 'how', 'why', 'when', 'where', 'who', 'which']):
        return True
    
    # Check if it's a simple greeting or social interaction
    social_words = ['hi', 'hello', 'hey', 'thanks', 'bye', 'good', 'nice', 'great', 'cool', 'awesome']
    if any(word in question_lower for word in social_words) and len(question.split()) <= 3:
        return True
    
    return False


async def is_followup_question(current_question: str, conversation_context: str, previous_query: str = None) -> dict:
    """
    Check if the current question is a follow-up to the previous conversation.
    Uses BOTH LLM-based checking AND semantic similarity for robust detection.
    
    Args:
        current_question: The new user question
        conversation_context: Previous conversation history
        previous_query: The immediately previous user question (for semantic similarity)
    
    Returns:
        dict: {
            'is_related': bool,  # True if follow-up, False if new topic
            'similarity_score': float,  # Semantic similarity score
            'llm_decision': str,  # LLM decision ('FOLLOWUP' or 'NEW')
            'needs_clarification': bool,  # True if ambiguous
            'clarification_message': str,  # Message to ask for clarification
            'current_topic': str,  # Detected topic of current question
            'previous_topic': str  # Detected topic from context
        }
    """
    if not conversation_context or len(conversation_context.strip()) == 0:
        # No previous conversation, so it can't be a follow-up
        return {
            'is_related': False,
            'similarity_score': 0.0,
            'llm_decision': 'NEW',
            'needs_clarification': False,
            'clarification_message': None,
            'current_topic': detect_query_topic(current_question),
            'previous_topic': None
        }
    
    try:
        # Extract previous query from conversation context if not provided
        if not previous_query and conversation_context:
            lines = conversation_context.split('\n')
            for line in reversed(lines):
                if line.startswith('User:'):
                    previous_query = line.replace('User:', '').strip()
                    break
        
        # Detect topics
        current_topic = detect_query_topic(current_question)
        previous_topic = detect_query_topic(previous_query) if previous_query else None
        
        print(f"[TOPIC DETECTION] Current: {current_topic}, Previous: {previous_topic}")
        
        # Check for ambiguous terms that need clarification
        needs_clarif, ambig_term, applicable_topics = needs_clarification(current_question, previous_topic)
        if needs_clarif:
            topic_names = {
                'google_workspace': 'Google Workspace',
                'dropbox_onedrive': 'Dropbox/OneDrive',
                'slack_teams': 'Slack/Teams',
                'box': 'Box',
                'sharepoint': 'SharePoint',
                's3': 'Amazon S3',
                'azure': 'Azure'
            }
            clarif_msg = f"I see you're asking about '{ambig_term}'. Are you referring to "
            clarif_msg += " or ".join([topic_names.get(t, t) for t in applicable_topics]) + "?"
            
            return {
                'is_related': False,
                'similarity_score': 0.0,
                'llm_decision': 'CLARIFICATION_NEEDED',
                'needs_clarification': True,
                'clarification_message': clarif_msg,
                'current_topic': current_topic,
                'previous_topic': previous_topic
            }
        
        # Explicit topic change detection
        if previous_topic and current_topic != previous_topic and current_topic != 'general':
            print(f"[TOPIC CHANGE] Switching from {previous_topic} to {current_topic}")
            return {
                'is_related': False,
                'similarity_score': 0.0,
                'llm_decision': 'TOPIC_CHANGE',
                'needs_clarification': False,
                'clarification_message': None,
                'current_topic': current_topic,
                'previous_topic': previous_topic
            }
        
        # Semantic similarity check
        similarity_score = 0.0
        is_similar_semantic = False
        if previous_query and SIMILARITY_MODEL:
            try:
                emb_new = SIMILARITY_MODEL.encode(current_question, convert_to_tensor=True)
                emb_prev = SIMILARITY_MODEL.encode(previous_query, convert_to_tensor=True)
                similarity_score = util.cos_sim(emb_new, emb_prev).item()
                is_similar_semantic = similarity_score >= 0.65
                print(f"[SEMANTIC SIMILARITY] Score: {similarity_score:.3f}")
            except Exception as e:
                print(f"[ERROR] Semantic similarity failed: {e}")
        
        # LLM-based relevance check
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.0, max_tokens=50)
        
        # Prompt to check if questions are related
        relevance_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a conversation analyzer. Determine if the current question is a follow-up to the previous conversation or a completely new topic.

A follow-up question (treat as FOLLOWUP):
- Refers to something mentioned in previous conversation
- Uses pronouns referring to previous context (e.g., "how does it work?", "tell me more")
- Asks for clarification or additional details about the previous topic
- Uses words like "also", "additionally", "what else"
- Generic questions about process when a specific topic was just discussed

A NEW topic (only treat as NEW if clearly different):
- Asks about a COMPLETELY DIFFERENT product/service/platform
- Has ZERO connection to previous topics discussed
- Explicitly switches context between platforms

Respond with ONLY one word: "FOLLOWUP" or "NEW"
"""),
            ("human", """Previous conversation:
{conversation_context}

Current question: {current_question}

Is this a follow-up or new topic?""")
        ])
        
        chain = relevance_prompt | llm
        result = await chain.ainvoke({
            "conversation_context": conversation_context[-500:],  # Last 500 chars to avoid token limits
            "current_question": current_question
        })
        
        response = result.content.strip().upper()
        is_related_llm = "FOLLOWUP" in response
        
        # DOUBLE GATING: Both checks must agree (unless similarity is very high)
        if similarity_score > 0.75:
            # Very high similarity - definitely related
            is_related = True
            final_decision = "FOLLOWUP (high similarity)"
        elif similarity_score < 0.50 and not is_related_llm:
            # Low similarity AND LLM says NEW - definitely new topic
            is_related = False
            final_decision = "NEW (low similarity + LLM)"
        else:
            # Use LLM decision but require semantic agreement
            is_related = is_related_llm and is_similar_semantic
            final_decision = f"{'FOLLOWUP' if is_related else 'NEW'} (LLM: {response}, Similarity: {similarity_score:.2f})"
        
        print(f"[RELEVANCE CHECK] Question: '{current_question[:50]}...'")
        print(f"[RELEVANCE CHECK] Result: {final_decision}")
        
        return {
            'is_related': is_related,
            'similarity_score': similarity_score,
            'llm_decision': response,
            'needs_clarification': False,
            'clarification_message': None,
            'current_topic': current_topic,
            'previous_topic': previous_topic
        }
        
    except Exception as e:
        print(f"[ERROR] Relevance check failed: {e}")
        # On error, assume it's related (safer default to maintain context when uncertain)
        return {
            'is_related': True,
            'similarity_score': 0.0,
            'llm_decision': 'ERROR',
            'needs_clarification': False,
            'clarification_message': None,
            'current_topic': detect_query_topic(current_question),
            'previous_topic': None
        }


def analyze_retrieved_documents(docs_with_scores):
    """Analyze retrieved documents and extract metadata."""
    if not docs_with_scores:
        return {
            "k_documents_retrieved": 0,
            "k_documents_used": 0,
            "sources_retrieved": {},
            "avg_similarity_score": 0.0,
            "top_similarity_score": 0.0,
            "lowest_similarity_score": 0.0,
            "sharepoint_docs_count": 0,
            "sharepoint_docs_percentage": 0.0,
            "sharepoint_folders": [],
            "blog_docs_count": 0,
            "pdf_docs_count": 0,
            "excel_docs_count": 0,
            "doc_docs_count": 0,
        }
    
    # Extract scores and sources
    scores = [score for _, score in docs_with_scores]
    sources_count = {}
    sharepoint_folders = set()
    sharepoint_count = 0
    blog_count = 0
    pdf_count = 0
    excel_count = 0
    doc_count = 0
    
    for doc, _ in docs_with_scores:
        # Determine source type from metadata
        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        source_type = metadata.get('source', 'unknown')
        
        # Count by source type
        if 'sharepoint' in source_type.lower():
            sharepoint_count += 1
            # Extract folder path
            tag = metadata.get('tag', '')
            if tag and tag.startswith('sharepoint/'):
                folder_path = tag.replace('sharepoint/', '').replace('/', ' > ')
                sharepoint_folders.add(folder_path)
        elif any(blog_indicator in source_type.lower() for blog_indicator in ['blog', 'wordpress', 'cloudfuze.com']):
            blog_count += 1
        elif 'pdf' in source_type.lower():
            pdf_count += 1
        elif 'excel' in source_type.lower() or 'xlsx' in source_type.lower():
            excel_count += 1
        elif 'doc' in source_type.lower():
            doc_count += 1
    
    total_docs = len(docs_with_scores)
    
    return {
        "k_documents_retrieved": total_docs,
        "k_documents_used": total_docs,  # After deduplication
        "sources_retrieved": {
            "sharepoint": sharepoint_count,
            "blog": blog_count,
            "pdf": pdf_count,
            "excel": excel_count,
            "doc": doc_count
        },
        "avg_similarity_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
        "top_similarity_score": round(max(scores), 3) if scores else 0.0,
        "lowest_similarity_score": round(min(scores), 3) if scores else 0.0,
        "sharepoint_docs_count": sharepoint_count,
        "sharepoint_docs_percentage": round((sharepoint_count / total_docs) * 100, 1) if total_docs > 0 else 0.0,
        "sharepoint_folders": list(sharepoint_folders)[:5],  # Limit to top 5 folders
        "blog_docs_count": blog_count,
        "pdf_docs_count": pdf_count,
        "excel_docs_count": excel_count,
        "doc_docs_count": doc_count,
    }

class ChatRequest(BaseModel):
    question: str
    user_id: str = None
    session_id: str = None  # Keep for backward compatibility
    user_name: str = None  # User's display name
    user_email: str = None  # User's email

class FeedbackRequest(BaseModel):
    trace_id: str
    rating: str  # "thumbs_up" or "thumbs_down"
    comment: str = None

@router.post("/chat/test")
async def chat_test(request: Request):
    """TESTING ONLY - Unprotected chat endpoint for automated testing. 
    Remove in production!"""
    data = await request.json()
    question = data.get("question", "")
    session_id = data.get("session_id", str(uuid.uuid4()))
    
    # Mock auth user for testing
    auth_user = {
        "user_id": "test_user",
        "email": "test@example.com",
        "name": "Test User"
    }
    
    # Use VERIFIED user info from mock auth
    user_id = auth_user["user_id"]
    user_name = auth_user["name"]
    user_email = auth_user["email"]

    # Use user_id if provided, otherwise fall back to session_id for backward compatibility
    conversation_id = user_id if user_id else session_id

    # HARD FILTER: Catch unrelated terms, single words, gibberish before processing
    clean_q = question.strip().lower()
    
    UNRELATED_TERMS = {
        "emoji", "emojis", "movie", "movies", "game", "games", "music",
        "sports", "weather", "food", "travel", "hello", "hey", "hi"
    }
    
    # If single word OR non alphabetic OR unrelated OR gibberish
    if (
        clean_q in UNRELATED_TERMS or
        len(clean_q.split()) == 1 or
        re.fullmatch(r"[^\w\s]+", clean_q) or  # punctuation only
        re.fullmatch(r"[a-zA-Z]{1,3}", clean_q)  # 1–3 random letters
    ):
        answer = (
            "I don't have specific information about that. "
            "I specialize in CloudFuze's migration services. "
            "What would you like to know?"
        )
        await add_to_conversation(conversation_id, "user", question)
        await add_to_conversation(conversation_id, "assistant", answer)
        return {"answer": answer, "session_id": session_id}

    # FIRST: Check if we have a corrected response for this question
    corrected_answer = find_similar_corrected_response(question)
    
    if corrected_answer:
        # Use the corrected response
        answer = corrected_answer
    # Check if this is a conversational query
    elif is_conversational_query(question):
        # Handle conversational queries directly without document retrieval
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)
        
        # Simple conversational prompt
        conversational_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are CloudFuze's AI assistant.

IMPORTANT:
- You must NEVER reply with generic greetings like "How are you?" or "How's your day?"
- You must ALWAYS introduce yourself as a CloudFuze assistant.
- All greetings MUST follow this exact pattern:

"Hi! 👋 I'm your CloudFuze assistant, here to help with CloudFuze migration services and products. What would you like to know about?"

REPEAT: NEVER say "How are you?" and NEVER act like a generic chatbot.

UNRELATED TOPICS OR SINGLE WORDS:
- If the query is a single word (e.g., "emojis", "books", "movies", "weather") or clearly unrelated to CloudFuze migration services, IMMEDIATELY redirect
- **MANDATORY RESPONSE**: "I don't have specific information about that. I specialize in CloudFuze's migration services. What would you like to know about?"
- **NEVER** try to answer unrelated queries like "emojis", "books", "movies", "weather", "recipes", "games", "music", "sports", "food", "travel", etc."""),
            ("human", "{question}")
        ])
        
        # Get conversation context for continuity
        conversation_context = await get_conversation_context(conversation_id)
        
        # Check if this question is related to previous conversation using both LLM + semantic similarity
        relevance_result = await is_followup_question(question, conversation_context)
        is_related = relevance_result['is_related']
        
        # Check if clarification is needed
        if relevance_result['needs_clarification']:
            answer = relevance_result['clarification_message']
            print(f"[CLARIFICATION NEEDED] {answer}")
            # Note: This returns early with clarification message
        
        # Only include conversation context if the question is a follow-up
        if is_related and conversation_context:
            enhanced_query = f"{conversation_context}\n\nUser: {question}"
            print(f"[CONTEXT] Using conversation history (related follow-up, similarity: {relevance_result['similarity_score']:.2f})")
        else:
            enhanced_query = question
            if relevance_result.get('previous_topic') and relevance_result.get('current_topic'):
                print(f"[CONTEXT] Starting fresh conversation (topic change: {relevance_result['previous_topic']} → {relevance_result['current_topic']})")
            else:
                print(f"[CONTEXT] Starting fresh conversation (new topic: {relevance_result.get('current_topic', 'general')})")
        
        chain = conversational_prompt | llm
        result = await chain.ainvoke({"question": enhanced_query})
        answer = result.content
    else:
        # Handle informational queries with document retrieval
        conversation_context = await get_conversation_context(conversation_id)
        
        # Check if this question is related to previous conversation using both LLM + semantic similarity
        relevance_result = await is_followup_question(question, conversation_context)
        is_related = relevance_result['is_related']
        
        # Check if clarification is needed
        if relevance_result['needs_clarification']:
            answer = relevance_result['clarification_message']
            print(f"[CLARIFICATION NEEDED] {answer}")
            # Note: This returns early with clarification message
        
        # Only include conversation context if the question is a follow-up
        if is_related and conversation_context:
            enhanced_query = f"{conversation_context}\n\nUser: {question}"
            print(f"[CONTEXT] Using conversation history (related follow-up, similarity: {relevance_result['similarity_score']:.2f})")
        else:
            enhanced_query = question
            if relevance_result.get('previous_topic') and relevance_result.get('current_topic'):
                print(f"[CONTEXT] Starting fresh conversation (topic change: {relevance_result['previous_topic']} → {relevance_result['current_topic']})")
            else:
                print(f"[CONTEXT] Starting fresh conversation (new topic: {relevance_result.get('current_topic', 'general')})")
        
        # Full RAG pipeline with unified retrieval
        if vectorstore is None:
            answer = "Vectorstore not initialized."
        else:
            try:
                # Use unified retrieval
                from app.unified_retrieval import unified_retrieve
                
                print(f"[UNIFIED RETRIEVAL] Processing test query")
                
                doc_results = unified_retrieve(
                    query=question,
                    vectorstore=vectorstore,
                    bm25_retriever=None,
                    k=50
                )
                
                # Get top documents
                top_docs = [doc for doc, score in doc_results[:30]]
                
                # Format context
                from app.llm import format_docs
                formatted_docs = format_docs(top_docs)
                context = "\n\n".join(formatted_docs)
                
                # Get prompt
                from app.prompt_manager import get_system_prompt, compile_prompt
                langfuse_prompt_template, prompt_metadata = get_system_prompt()
                
                # Generate answer
                from langchain_openai import ChatOpenAI
                from langchain_core.prompts import ChatPromptTemplate
                
                llm = ChatOpenAI(
                    model_name="gpt-4o-mini",
                    streaming=False,
                    temperature=0.3,
                    max_tokens=1500
                )
                
                if langfuse_prompt_template:
                    try:
                        # compile_prompt already returns escaped text for LangChain
                        compiled_prompt_text = compile_prompt(
                            langfuse_prompt_template,
                            context=context,
                            question=enhanced_query
                        )
                        prompt_template = ChatPromptTemplate.from_messages([
                            ("system", compiled_prompt_text)
                        ])
                        chain = prompt_template | llm
                        result = await chain.ainvoke({})


                        
                    except Exception as prompt_error:
                        print(f"[WARNING] Langfuse prompt failed: {prompt_error}")
                        print("[FALLBACK] Using local SYSTEM_PROMPT")
                        from config import SYSTEM_PROMPT
                        prompt_template = ChatPromptTemplate.from_messages([
                            ("system", SYSTEM_PROMPT),
                            ("human", "Context: {context}\n\nQuestion: {question}")
                        ])
                        chain = prompt_template | llm
                        result = await chain.ainvoke({
                            "context": context,
                            "question": enhanced_query
                        })
                else:
                    from config import SYSTEM_PROMPT
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", SYSTEM_PROMPT),
                        ("human", "Context: {context}\n\nQuestion: {question}")
                    ])
                    chain = prompt_template | llm
                    result = await chain.ainvoke({
                        "context": context,
                        "question": enhanced_query
                    })
                
                answer = normalize_chain_output(result)
                
            except Exception as e:
                print(f"[ERROR] RAG pipeline failed: {e}")
                answer = f"Error processing question: {str(e)}"

    # Add both user question and bot response to conversation AFTER processing
    await add_to_conversation(conversation_id, "user", question)
    await add_to_conversation(conversation_id, "assistant", answer)

    return {
        "answer": answer,
        "session_id": session_id,
        "trace_id": "test_trace",
        "test_mode": True
    }


@router.post("/chat")
async def chat(request: Request, auth_user: dict = Depends(require_auth)):
    """Chat endpoint: returns full answer from vectorstore. PROTECTED - requires valid authentication."""
    data = await request.json()
    question = data.get("question", "")
    session_id = data.get("session_id", str(uuid.uuid4()))
    
    # Use VERIFIED user info from auth token, NOT from request body
    user_id = auth_user["user_id"]
    user_name = auth_user["name"]
    user_email = auth_user["email"]

    # Use user_id if provided, otherwise fall back to session_id for backward compatibility
    conversation_id = user_id if user_id else session_id

    # HARD FILTER: Catch unrelated terms, single words, gibberish before processing
    clean_q = question.strip().lower()
    
    UNRELATED_TERMS = {
        "emoji", "emojis", "movie", "movies", "game", "games", "music",
        "sports", "weather", "food", "travel", "hello", "hey", "hi"
    }
    
    # If single word OR non alphabetic OR unrelated OR gibberish
    if (
        clean_q in UNRELATED_TERMS or
        len(clean_q.split()) == 1 or
        re.fullmatch(r"[^\w\s]+", clean_q) or  # punctuation only
        re.fullmatch(r"[a-zA-Z]{1,3}", clean_q)  # 1–3 random letters
    ):
        answer = (
            "I don't have specific information about that. "
            "I specialize in CloudFuze's migration services. "
            "What would you like to know?"
        )
        await add_to_conversation(conversation_id, "user", question)
        await add_to_conversation(conversation_id, "assistant", answer)
        return {"answer": answer, "user_id": user_id, "session_id": session_id}

    # FIRST: Check if we have a corrected response for this question
    corrected_answer = find_similar_corrected_response(question)
    
    if corrected_answer:
        # Use the corrected response
        answer = corrected_answer
    # Check if this is a conversational query
    elif is_conversational_query(question):
        # Handle conversational queries directly without document retrieval
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)
        
        # Simple conversational prompt
        conversational_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are CloudFuze's AI assistant.

IMPORTANT:
- You must NEVER reply with generic greetings like "How are you?" or "How's your day?"
- You must ALWAYS introduce yourself as a CloudFuze assistant.
- All greetings MUST follow this exact pattern:

"Hi! 👋 I'm your CloudFuze assistant, here to help with CloudFuze migration services and products. What would you like to know about?"

REPEAT: NEVER say "How are you?" and NEVER act like a generic chatbot.

UNRELATED TOPICS OR SINGLE WORDS:
- If the query is a single word (e.g., "emojis", "books", "movies", "weather") or clearly unrelated to CloudFuze migration services, IMMEDIATELY redirect
- **MANDATORY RESPONSE**: "I don't have specific information about that. I specialize in CloudFuze's migration services. What would you like to know about?"
- **NEVER** try to answer unrelated queries like "emojis", "books", "movies", "weather", "recipes", "games", "music", "sports", "food", "travel", etc."""),
            ("human", "{question}")
        ])
        
        # Get conversation context for continuity
        conversation_context = await get_conversation_context(conversation_id)
        
        # Check if this question is related to previous conversation using both LLM + semantic similarity
        relevance_result = await is_followup_question(question, conversation_context)
        is_related = relevance_result['is_related']
        
        # Check if clarification is needed
        if relevance_result['needs_clarification']:
            answer = relevance_result['clarification_message']
            print(f"[CLARIFICATION NEEDED] {answer}")
            # Note: This returns early with clarification message
        
        # Only include conversation context if the question is a follow-up
        if is_related and conversation_context:
            enhanced_query = f"{conversation_context}\n\nUser: {question}"
            print(f"[CONTEXT] Using conversation history (related follow-up, similarity: {relevance_result['similarity_score']:.2f})")
        else:
            enhanced_query = question
            if relevance_result.get('previous_topic') and relevance_result.get('current_topic'):
                print(f"[CONTEXT] Starting fresh conversation (topic change: {relevance_result['previous_topic']} → {relevance_result['current_topic']})")
            else:
                print(f"[CONTEXT] Starting fresh conversation (new topic: {relevance_result.get('current_topic', 'general')})")
        
        chain = conversational_prompt | llm
        result = await chain.ainvoke({"question": enhanced_query})
        answer = result.content
    else:
        # Handle informational queries with document retrieval
        conversation_context = await get_conversation_context(conversation_id)
        
        # Check if this question is related to previous conversation using both LLM + semantic similarity
        relevance_result = await is_followup_question(question, conversation_context)
        is_related = relevance_result['is_related']
        
        # Check if clarification is needed
        if relevance_result['needs_clarification']:
            answer = relevance_result['clarification_message']
            print(f"[CLARIFICATION NEEDED] {answer}")
            # Note: This returns early with clarification message
        
        # Only include conversation context if the question is a follow-up
        if is_related and conversation_context:
            enhanced_query = f"{conversation_context}\n\nUser: {question}"
            print(f"[CONTEXT] Using conversation history (related follow-up, similarity: {relevance_result['similarity_score']:.2f})")
        else:
            enhanced_query = question
            if relevance_result.get('previous_topic') and relevance_result.get('current_topic'):
                print(f"[CONTEXT] Starting fresh conversation (topic change: {relevance_result['previous_topic']} → {relevance_result['current_topic']})")
            else:
                print(f"[CONTEXT] Starting fresh conversation (new topic: {relevance_result.get('current_topic', 'general')})")
        
        # Check if vectorstore is available
        if vectorstore is None:
            print("Warning: Vectorstore not initialized. Using default qa_chain.")
            result = qa_chain.invoke({"query": enhanced_query})
            answer = normalize_chain_output(result)
        else:
            try:
                # ============ UNIFIED RETRIEVAL ============
                # Use unified hybrid retrieval (replaces intent-based branching)
                from app.unified_retrieval import unified_retrieve
                
                print(f"[UNIFIED RETRIEVAL] Processing query with full knowledge base")
                
                # Retrieve documents with unified pipeline
                RETRIEVAL_K = 50  # Number of documents to retrieve from vectorstore
                doc_results = unified_retrieve(
                    query=question,  # Use original question
                    vectorstore=vectorstore,
                    bm25_retriever=None,  # Optional: add BM25 if available
                    k=RETRIEVAL_K
                )
                
                print(f"[RETRIEVAL] Retrieved {len(doc_results)} documents via unified pipeline")
                
                # ============ DOCUMENT DIVERSITY ============
                # Calculate diversity metrics for retrieved documents
                diversity_metrics = calculate_document_diversity(doc_results)
                print(f"[DIVERSITY] Overall: {diversity_metrics['overall']:.2f}, Sources: {diversity_metrics['unique_sources']}, Tags: {diversity_metrics['unique_tags']}")
                
                final_docs = [doc for doc, score in doc_results]  # Extract just the documents
                
                # Format the documents for the context
                from app.llm import format_docs
                formatted_docs = format_docs(final_docs)
                context = "\n\n".join(formatted_docs)
                
                # Create prompt and get answer
                from langchain_core.prompts import ChatPromptTemplate
                from langchain_openai import ChatOpenAI
                from config import SYSTEM_PROMPT
                
                # Try to get prompt from Langfuse (non-breaking addition)
                langfuse_prompt_template, prompt_metadata = get_system_prompt()
                
                llm = ChatOpenAI(
                    model_name="gpt-4o-mini",
                    temperature=0.3,
                    max_tokens=1500
                )
                
                if langfuse_prompt_template:
                    # Use Langfuse prompt (context and question already compiled)
                    try:
                        # compile_prompt already returns escaped text for LangChain
                        compiled_prompt_text = compile_prompt(
                            langfuse_prompt_template,
                            context=context,
                            question=enhanced_query
                        )
                        prompt_template = ChatPromptTemplate.from_messages([
                            ("system", compiled_prompt_text)
                        ])
                        chain = prompt_template | llm
                        result = await chain.ainvoke({})  # No variables needed
                    except Exception as prompt_error:
                        print(f"[WARNING] Langfuse prompt failed: {prompt_error}")
                        print("[FALLBACK] Using local SYSTEM_PROMPT")
                        # Fallback to existing behavior
                        prompt_template = ChatPromptTemplate.from_messages([
                            ("system", SYSTEM_PROMPT),
                            ("human", "Context: {context}\n\nQuestion: {question}")
                        ])
                        chain = prompt_template | llm
                        result = await chain.ainvoke({
                            "context": context,
                            "question": enhanced_query
                        })
                else:
                    # Fallback to existing behavior
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", SYSTEM_PROMPT),
                        ("human", "Context: {context}\n\nQuestion: {question}")
                    ])
                    chain = prompt_template | llm
                    result = await chain.ainvoke({
                        "context": context,
                        "question": enhanced_query
                    })
                
                answer = normalize_chain_output(result)
                
            except Exception as e:
                print(f"[ERROR] Intent-based retrieval failed: {e}")
                # Fallback to original qa_chain if something goes wrong
                result = qa_chain.invoke({"query": enhanced_query})
                answer = normalize_chain_output(result)

    # Add both user question and bot response to conversation AFTER processing
    await add_to_conversation(conversation_id, "user", question)
    await add_to_conversation(conversation_id, "assistant", answer)

    # Log to Langfuse for observability
    trace_id = langfuse_tracker.create_trace(
        user_id=conversation_id,
        question=question,
        answer=answer,
        session_id=session_id,
        user_name=user_name,
        user_email=user_email,
        metadata={
            "user_id": user_id or "anonymous",
            "session_id": session_id,
            "user_name": user_name,
            "user_email": user_email,
            "request": {
            "endpoint": "/chat",
                "timestamp": datetime.now().isoformat()
            },
            "query": {
                "is_conversational": is_conversational_query(question)
            }
        }
    )

    clean_answer = preserve_markdown(answer)
    return {"answer": clean_answer, "user_id": user_id, "session_id": session_id, "trace_id": trace_id}

# ---------------- Streaming Chat Endpoint ----------------

@router.post("/chat/stream")
async def chat_stream(request: Request, auth_user: dict = Depends(require_auth)):
    """Streaming chat endpoint. PROTECTED - requires valid authentication."""
    data = await request.json()
    question = data.get("question", "")
    session_id = data.get("session_id", str(uuid.uuid4()))
    
    # Use VERIFIED user info from auth token, NOT from request body
    user_id = auth_user["user_id"]
    user_name = auth_user["name"]
    user_email = auth_user["email"]

    # Use user_id if provided, otherwise fall back to session_id for backward compatibility
    conversation_id = user_id if user_id else session_id

    async def generate_stream():
        try:
            # FIRST: Check if we have a corrected response for this question
            corrected_answer = find_similar_corrected_response(question)
            
            if corrected_answer:
                # Use the corrected response
                yield f"data: {json.dumps({'type': 'thinking_complete'})}\n\n"
                
                # Stream the corrected answer token by token
                full_response = corrected_answer
                for i, char in enumerate(corrected_answer):
                    yield f"data: {json.dumps({'token': char, 'type': 'token'})}\n\n"
                    if i % 5 == 0:  # Add slight delay every 5 characters
                        await asyncio.sleep(0.01)
                
                # Add to conversation
                await add_to_conversation(conversation_id, "user", question)
                await add_to_conversation(conversation_id, "assistant", full_response)
                
                # Log to Langfuse
                trace_id = None
                try:
                    trace_id = langfuse_tracker.create_trace(
                        user_id=conversation_id,
                        question=question,
                        answer=full_response,
                        session_id=session_id,
                        user_name=user_name,
                        user_email=user_email,
                        metadata={
                            "user_id": user_id or "anonymous",
                            "session_id": session_id,
                            "user_name": user_name,
                            "user_email": user_email,
                            "request": {
                            "endpoint": "/chat/stream",
                                "timestamp": datetime.now().isoformat()
                            },
                            "system": {
                            "used_corrected_response": True
                            }
                        }
                    )
                except Exception as e:
                    print(f"Warning: Langfuse logging failed: {e}")
                
                yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'trace_id': trace_id})}\n\n"
                return
            
            # Get conversation context BEFORE adding current question
            conversation_context = await get_conversation_context(conversation_id)

            # Check if this question is related to previous conversation
            is_related = await is_followup_question(question, conversation_context)
            
            # Only include conversation context if the question is a follow-up
            if is_related and conversation_context:
                enhanced_query = f"{conversation_context}\n\nUser: {question}"
                print(f"[CONTEXT] Using conversation history (related follow-up)")
            else:
                enhanced_query = question
                print(f"[CONTEXT] Starting fresh conversation (new topic)")
            
            # Check if this is a conversational query
            is_conv = is_conversational_query(question)
            
            if is_conv:
                # Handle conversational queries directly without document retrieval
                yield f"data: {json.dumps({'type': 'thinking_complete'})}\n\n"
                
                from langchain_openai import ChatOpenAI
                from langchain_core.prompts import ChatPromptTemplate
                
                llm = ChatOpenAI(
                    model_name="gpt-4o-mini", 
                    streaming=True, 
                    temperature=0.7,
                    max_tokens=500
                )
                
                # Simple conversational prompt
                conversational_prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are CloudFuze's AI assistant.

IMPORTANT:
- You must NEVER reply with generic greetings like "How are you?" or "How's your day?"
- You must ALWAYS introduce yourself as a CloudFuze assistant.
- All greetings MUST follow this exact pattern:

"Hi! 👋 I'm your CloudFuze assistant, here to help with CloudFuze migration services and products. What would you like to know about?"

REPEAT: NEVER say "How are you?" and NEVER act like a generic chatbot.

UNRELATED TOPICS OR SINGLE WORDS:
- If the query is a single word (e.g., "emojis", "books", "movies", "weather") or clearly unrelated to CloudFuze migration services, IMMEDIATELY redirect
- **MANDATORY RESPONSE**: "I don't have specific information about that. I specialize in CloudFuze's migration services. What would you like to know about?"
- **NEVER** try to answer unrelated queries like "emojis", "books", "movies", "weather", "recipes", "games", "music", "sports", "food", "travel", etc."""),
                    ("human", "{question}")
                ])
                
                # Stream the response
                full_response = ""
                messages = conversational_prompt.format_messages(question=enhanced_query)
                try:
                    async for chunk in llm.astream(messages):
                        if hasattr(chunk, 'content'):
                            token = chunk.content
                            full_response += token
                            yield f"data: {json.dumps({'token': token, 'type': 'token'})}\n\n"
                            await asyncio.sleep(0.01)
                except (httpx.ReadError, httpx.ReadTimeout, httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException, httpx.NetworkError) as stream_error:
                    # Network error during streaming - send what we have so far
                    print(f"[WARNING] Streaming interrupted by network error: {stream_error}")
                    if full_response:
                        yield f"data: {json.dumps({'type': 'warning', 'message': 'Connection interrupted, but partial response received'})}\n\n"
                    else:
                        error_msg = "I apologize, but there was a connection issue while generating the response. Please try again."
                        full_response = error_msg
                        yield f"data: {json.dumps({'token': error_msg, 'type': 'token'})}\n\n"
                except Exception as stream_error:
                    # Other streaming errors
                    print(f"[WARNING] Streaming error: {stream_error}")
                    if not full_response:
                        error_msg = "I encountered an error while generating the response. Please try again."
                        full_response = error_msg
                        yield f"data: {json.dumps({'token': error_msg, 'type': 'token'})}\n\n"
                
                # Add to conversation
                await add_to_conversation(conversation_id, "user", question)
                await add_to_conversation(conversation_id, "assistant", full_response)
                
                # Log to Langfuse (don't block response if this fails)
                trace_id = None
                try:
                    trace_id = langfuse_tracker.create_trace(
                        user_id=conversation_id,
                        question=question,
                        answer=full_response,
                        session_id=session_id,
                        user_name=user_name,
                        user_email=user_email,
                        metadata={
                            "user_id": user_id or "anonymous",
                            "session_id": session_id,
                            "user_name": user_name,
                            "user_email": user_email,
                            "request": {
                            "endpoint": "/chat/stream",
                                "timestamp": datetime.now().isoformat()
                            },
                            "query": {
                                "is_conversational": True
                            },
                            "generation": {
                                "model": "gpt-4o-mini",
                            "streaming": True
                            }
                        }
                    )
                except Exception as e:
                    print(f"Langfuse logging failed: {e}")
                
                # Send completion signal with trace_id
                yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'trace_id': trace_id})}\n\n"
                return
            
            # ===== LOAD PROMPT FROM LANGFUSE =====
            # Load prompt before creating trace so we can link them
            langfuse_prompt_template, prompt_metadata = get_system_prompt()
            
            # ===== START RAG PIPELINE TRACING =====
            # Create structured Langfuse trace for RAG pipeline with prompt tracking
            rag_trace = None
            try:
                rag_trace = langfuse_tracker.create_rag_pipeline_trace(
                    user_id=conversation_id,
                    question=question,
                    session_id=session_id,
                    user_name=user_name,
                    user_email=user_email,
                    metadata={
                        "endpoint": "/chat/stream",
                        "conversational_query": False,
                        "streaming": True
                    },
                    prompt_template=langfuse_prompt_template,
                    prompt_metadata=prompt_metadata
                )
                
                # Start query processing span
                if rag_trace:
                    rag_trace.start_query(enhanced_query, metadata={"has_conversation_context": bool(conversation_context)})
            except Exception as e:
                print(f"[WARNING] Failed to create RAG trace: {e}")
                rag_trace = None
            
            # PHASE 1: THINKING - Document retrieval and processing
            # This happens while the frontend shows "Thinking..." animation
            
            # Start timing for metadata
            retrieval_start_time = time.time()
            thinking_start_time = time.time()
            
            # Configuration for document retrieval
            RETRIEVAL_K = 50  # Number of documents to retrieve from vectorstore
            
            # Initialize metadata collectors
            query_classification = {
                "query_type": classify_query_type(question),
                "query_category": classify_query_category(question),
                "query_intent": "unknown",  # CRITICAL: Prevents KeyError at line 1751
                "is_conversational_query": is_conv,
                "query_length_words": len(question.split()),
                "query_length_chars": len(question),
                "has_followup": bool(conversation_context),
            }
            
            try:
                # ============ UNIFIED RETRIEVAL ============
                # Use unified hybrid retrieval (replaces intent-based branching)
                from app.unified_retrieval import unified_retrieve
                
                print(f"[UNIFIED RETRIEVAL] Processing query with full knowledge base")
                
                # Check if vectorstore is available
                if vectorstore is None:
                    print("Warning: Vectorstore not initialized. Please rebuild vectorstore manually.")
                    final_docs = []
                    doc_results = []
                    diversity_metrics = {}
                else:
                    # Retrieve documents with unified pipeline
                    doc_results = unified_retrieve(
                        query=question,  # Use original question
                        vectorstore=vectorstore,
                        bm25_retriever=None,  # Optional: add BM25 if available
                        k=RETRIEVAL_K
                    )
                    
                    print(f"[RETRIEVAL] Retrieved {len(doc_results)} documents via unified pipeline")
                    
                    print(f"[HYBRID RANKING] Reranked {len(doc_results)} documents with semantic + keyword scores")
                    
                    # ============ DOCUMENT DIVERSITY ============
                    # Calculate diversity metrics for retrieved documents
                    diversity_metrics = calculate_document_diversity(doc_results)
                    print(f"[DIVERSITY] Overall: {diversity_metrics['overall']:.2f}, Sources: {diversity_metrics['unique_sources']}, Tags: {diversity_metrics['unique_tags']}")
                    
                    final_docs = [doc for doc, score in doc_results]  # Extract just the documents (already sorted by relevance)
                    
                # Record retrieval time
                retrieval_time_ms = int((time.time() - retrieval_start_time) * 1000)
                
                # Log what sources we're retrieving (for backend debugging)
                retrieved_sources = {}
                for doc in final_docs:
                    tag = doc.metadata.get('tag', 'unknown')
                    source_type = doc.metadata.get('source_type', 'unknown')
                    if tag not in retrieved_sources:
                        retrieved_sources[tag] = 0
                    retrieved_sources[tag] += 1
                
                print(f"[DEBUG] Retrieved {len(final_docs)} documents from search")
                print(f"[DEBUG] Documents by tag: {retrieved_sources}")
                
                # If no SharePoint documents found, try a more aggressive search for SharePoint content
                has_sharepoint = any(
                    doc.metadata.get('source_type') == 'sharepoint' or 
                    'sharepoint' in doc.metadata.get('tag', '').lower()
                    for doc in final_docs
                )
                
                if not has_sharepoint and any(word in enhanced_query.lower() for word in ['sharepoint', 'document', 'file', 'folder', 'download', 'certificate']) and vectorstore is not None:
                    print("[DEBUG] No SharePoint docs found - trying SharePoint-specific search...")
                    try:
                        # Try searching for SharePoint content with modified queries
                        sharepoint_docs = vectorstore.similarity_search(enhanced_query + " SharePoint", k=30)
                        # Filter results to only SharePoint documents
                        sharepoint_docs = [d for d in sharepoint_docs if d.metadata.get('source_type') == 'sharepoint']
                        if sharepoint_docs:
                            print(f"[DEBUG] Found {len(sharepoint_docs)} SharePoint documents with filter")
                            # Add SharePoint docs to results (prioritize them)
                            final_docs = sharepoint_docs[:10] + final_docs
                            print(f"[DEBUG] Updated total: {len(final_docs)} documents")
                    except Exception as e:
                        print(f"[DEBUG] Filtered search failed (this is OK): {e}")
                        # Try search with different query variations
                        try:
                            sharepoint_queries = [
                                enhanced_query + " SharePoint",
                                enhanced_query + " document",
                                enhanced_query.replace("?", "").replace("how", "what")
                            ]
                            for sp_query in sharepoint_queries[:2]:
                                if vectorstore is not None:
                                    sp_docs = vectorstore.similarity_search(sp_query, k=15)
                                # Filter for SharePoint docs
                                sp_filtered = [d for d in sp_docs if d.metadata.get('source_type') == 'sharepoint']
                                if sp_filtered:
                                    final_docs.extend(sp_filtered[:5])
                                    break
                        except Exception as e2:
                            print(f"[DEBUG] Alternative search failed: {e2}")
            except Exception as e:
                print(f"Error during document search: {e}")
                final_docs = []
            
            # Deduplicate documents while preserving relevance order (prioritize SharePoint if found)
            seen_ids = set()
            unique_docs = []
            
            # First, add SharePoint documents if any
            for doc in final_docs:
                if doc.metadata.get('source_type') == 'sharepoint':
                    doc_id = f"{doc.metadata.get('source', '')}_{doc.metadata.get('file_name', '')}_{doc.page_content[:100]}"
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        unique_docs.append(doc)
            
            # Then add other documents
            for doc in final_docs:
                if doc.metadata.get('source_type') != 'sharepoint':
                    doc_id = f"{doc.metadata.get('source', '')}_{doc.page_content[:100]}"
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        unique_docs.append(doc)
            
            # Limit to top 30 documents for LLM processing
            final_docs = unique_docs[:30]
            
            print(f"[DEBUG] Final documents for context: {len(final_docs)} (after deduplication)")
            
            # Analyze final documents after deduplication for accurate metadata
            # We need to pair final_docs with their scores from doc_results
            final_docs_with_scores = []
            for final_doc in final_docs:
                # Find the matching doc in doc_results to get its score
                for doc, score in doc_results:
                    if doc.page_content == final_doc.page_content:
                        final_docs_with_scores.append((final_doc, score))
                        break
            
            doc_analysis = analyze_retrieved_documents(final_docs_with_scores)
            
            # ===== LOG RETRIEVAL TO LANGFUSE =====
            if rag_trace:
                try:
                    # Calculate sources breakdown for tracing
                    trace_sources = {}
                    for doc in final_docs:
                        source_type = doc.metadata.get('source_type', 'unknown')
                        tag = doc.metadata.get('tag', 'unknown')
                        key = f"{source_type}:{tag}"
                        trace_sources[key] = trace_sources.get(key, 0) + 1
                    
                    rag_trace.log_retrieval(
                        query=enhanced_query,
                        retrieved_docs=final_docs,
                        doc_count=len(final_docs),
                        sources_breakdown=trace_sources,
                        metadata={"search_k": 50, "final_k": len(final_docs)}
                    )
                except Exception as e:
                    print(f"[WARNING] Failed to log retrieval: {e}")
            
            # Format the documents properly with metadata using format_docs from llm.py
            try:
                from app.llm import format_docs
                
                if not final_docs:
                    print("[WARNING] No documents retrieved for context!")
                    context_text = "No relevant documents found in the knowledge base."
                else:
                    formatted_docs = format_docs(final_docs)
                    context_text = "\n\n".join([f"Document {i+1}:\n{formatted_doc}" for i, formatted_doc in enumerate(formatted_docs)])
                    print(f"[DEBUG] Context length: {len(context_text)} characters")
                    print(f"[DEBUG] First 500 chars of context: {context_text[:500]}...")
            except Exception as e:
                print(f"[ERROR] Failed to format documents: {e}")
                import traceback
                traceback.print_exc()
                # Fallback: use raw document content
                context_text = "\n\n".join([f"Document {i+1}:\n{doc.page_content}" for i, doc in enumerate(final_docs[:10])])
            
            # Extract source information for console logging - only from TOP relevant documents
            # Use top 10 most relevant documents (best similarity scores) to determine sources
            top_relevant_count = min(10, len(final_docs))
            top_relevant_docs = final_docs[:top_relevant_count]
            
            # Track unique sources from top relevant documents only
            sources_seen = set()
            sources_used = []
            for doc in top_relevant_docs:
                tag = doc.metadata.get('tag', 'unknown')
                source_type = doc.metadata.get('source_type', 'unknown')
                
                # Create a clean source identifier
                if source_type == 'sharepoint':
                    folder_path = doc.metadata.get('folder_path', '')
                    if folder_path:
                        # Use full folder path for clarity
                        source_id = f"SharePoint: {folder_path}"
                    else:
                        source_id = 'SharePoint'
                elif tag == 'blog':
                    source_id = 'Blog Content'
                elif tag == 'pdf':
                    source_id = 'PDF Documents'
                elif tag == 'excel':
                    source_id = 'Excel Documents'
                elif tag == 'doc':
                    source_id = 'Word Documents'
                else:
                    source_id = tag.replace('_', ' ').title()
                
                # Only add unique sources
                if source_id not in sources_seen:
                    sources_seen.add(source_id)
                    sources_used.append(source_id)
            
            # Format source info for console
            if sources_used:
                source_info = f"Response generated from: {', '.join(sources_used)}"
            else:
                source_info = "Response generated (sources unknown)"
            
            # Send signal that thinking is complete and streaming will start
            thinking_time_ms = int((time.time() - thinking_start_time) * 1000)
            yield f"data: {json.dumps({'type': 'thinking_complete'})}\n\n"
            
            # Send source information for console logging
            yield f"data: {json.dumps({'type': 'sources', 'sources': source_info})}\n\n"
            
            # Collect context preparation metadata
            context_size_chars = len(context_text)
            context_size_tokens = context_size_chars // 4  # Rough approximation
            
            # PHASE 2: STREAMING - Generate and stream response
            # This happens after the frontend clears the "Thinking..." animation
            llm_start_time = time.time()
            
            # Import ChatOpenAI for document-based queries
            from langchain_openai import ChatOpenAI
            
            # Create streaming LLM
            llm = ChatOpenAI(
                model_name="gpt-4o-mini", 
                streaming=True, 
                temperature=0.3,
                max_tokens=1500
            )
            
            # Create the prompt template
            from langchain_core.prompts import ChatPromptTemplate
            from config import SYSTEM_PROMPT
            
            # Use prompt already loaded at the start (linked to trace)
            if langfuse_prompt_template:
                # Use Langfuse prompt
                # compile_prompt already returns escaped text for LangChain
                compiled_prompt_text = compile_prompt(
                    langfuse_prompt_template,
                    context=context_text,
                    question=enhanced_query
                )
                # Create messages from compiled prompt with error handling
                try:
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", compiled_prompt_text)
                    ])
                    messages = prompt_template.format_messages()
                except Exception as prompt_error:
                    print(f"[WARNING] Langfuse prompt formatting failed: {prompt_error}")
                    print("[FALLBACK] Using local SYSTEM_PROMPT instead")
                    # Fallback to local prompt
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", SYSTEM_PROMPT),
                        ("human", "Context: {context}\n\nQuestion: {question}")
                    ])
                    messages = prompt_template.format_messages(context=context_text, question=enhanced_query)
            else:
                # Fallback to existing behavior
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", SYSTEM_PROMPT),
                    ("human", "Context: {context}\n\nQuestion: {question}")
                ])
                messages = prompt_template.format_messages(context=context_text, question=enhanced_query)
            
            # ===== START SYNTHESIS SPAN =====
            if rag_trace:
                try:
                    rag_trace.start_synthesis(
                        context=context_text,
                        metadata={
                            "context_length": len(context_text),
                            "document_count": len(final_docs),
                            "model": "gpt-4o-mini",
                            "temperature": 0.3
                        }
                    )
                except Exception as e:
                    print(f"[WARNING] Failed to start synthesis: {e}")
            
            # Stream the response with real-time streaming
            full_response = ""
            # Messages already created above based on prompt source
            try:
                async for chunk in llm.astream(messages):
                    if hasattr(chunk, 'content'):
                        token = chunk.content
                        full_response += token
                        yield f"data: {json.dumps({'token': token, 'type': 'token'})}\n\n"
                        await asyncio.sleep(0.01)  # Small delay for better streaming effect
            except (httpx.ReadError, httpx.ReadTimeout, httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException, httpx.NetworkError) as stream_error:
                # Network error during streaming - send what we have so far
                print(f"[WARNING] Streaming interrupted by network error: {stream_error}")
                if full_response:
                    # If we got some response, send it and complete gracefully
                    yield f"data: {json.dumps({'type': 'warning', 'message': 'Connection interrupted, but partial response received'})}\n\n"
                else:
                    # No response received, send error
                    error_msg = "I apologize, but there was a connection issue while generating the response. Please try again."
                    full_response = error_msg
                    yield f"data: {json.dumps({'token': error_msg, 'type': 'token'})}\n\n"
            except Exception as stream_error:
                # Other streaming errors
                print(f"[WARNING] Streaming error: {stream_error}")
                if not full_response:
                    error_msg = "I encountered an error while generating the response. Please try again."
                    full_response = error_msg
                    yield f"data: {json.dumps({'token': error_msg, 'type': 'token'})}\n\n"
            
            # Record LLM generation time
            llm_time_ms = int((time.time() - llm_start_time) * 1000)
            streaming_time_ms = llm_time_ms  # In streaming mode, these are the same
            
            # Add both user question and bot response to conversation AFTER processing
            await add_to_conversation(conversation_id, "user", question)
            await add_to_conversation(conversation_id, "assistant", full_response)
            
            # Calculate total response time
            total_time_ms = thinking_time_ms + llm_time_ms
            
            # Calculate overall confidence score
            avg_similarity = doc_analysis.get("avg_similarity_score", 0.5)
            # Simple confidence calculation for unified retrieval
            doc_confidence = min(len(final_docs) / 30.0, 1.0)
            similarity_confidence = max(0, 1.0 - avg_similarity)
            overall_confidence = round((0.95 * 0.5) + (doc_confidence * 0.3) + (similarity_confidence * 0.2), 3)
            
            # ===== BUILD COMPREHENSIVE METADATA (NESTED STRUCTURE) =====
            comprehensive_metadata = {
                # User info at top level for easy filtering
                "user_id": user_id or "anonymous",
                "session_id": session_id,
                "user_name": user_name,
                "user_email": user_email,
                
                "request": {
                    "endpoint": "/chat/stream",
                    "timestamp": datetime.now().isoformat()
                },
                
                # ===== UNIFIED RETRIEVAL (NEW) =====
                "retrieval_method": {
                    "type": "unified_hybrid_retrieval",
                    "description": "Unified retrieval without intent classification",
                    "confidence": 0.95
                },
                
                # ===== CONFIDENCE SCORING (NEW) =====
                "confidence": {
                    "overall": overall_confidence,
                    "breakdown": {
                        "unified_retrieval": 0.95,
                        "document_count": min(len(final_docs) / 30.0, 1.0),
                        "similarity": max(0, 1.0 - avg_similarity) if avg_similarity else 0.5
                    }
                },
                
                "query": {
                    "classification": {
                        "type": query_classification["query_type"],
                        "category": query_classification["query_category"],
                        "intent": query_classification["query_intent"],
                        "is_conversational": query_classification["is_conversational_query"]
                    },
                    "metrics": {
                        "length_words": query_classification["query_length_words"],
                        "length_chars": query_classification["query_length_chars"],
                        "has_followup": query_classification["has_followup"]
                    }
                },
                
                "retrieval": {
                    "method": "unified_hybrid_retrieval",
                    "techniques_applied": ["keyword_detection", "ngram_boosting", "vector_search", "metadata_filtering", "diversity_scoring"],
                    "query_info": {
                        "original": question,
                        "enhanced": enhanced_query if 'enhanced_query' in locals() else question
                    },
                    "documents": {
                        "requested": RETRIEVAL_K,
                        "retrieved": doc_analysis["k_documents_retrieved"],
                        "used": doc_analysis["k_documents_used"]
                    },
                    "similarity_scores": {
                        "avg": doc_analysis["avg_similarity_score"],
                        "top": doc_analysis["top_similarity_score"],
                        "lowest": doc_analysis["lowest_similarity_score"]
                    },
                    "diversity": diversity_metrics if diversity_metrics else {},
                    "sources": doc_analysis["sources_retrieved"],
                    "sharepoint": {
                        "count": doc_analysis["sharepoint_docs_count"],
                        "percentage": doc_analysis["sharepoint_docs_percentage"],
                        "folders": doc_analysis["sharepoint_folders"]
                    },
                    "blog_count": doc_analysis["blog_docs_count"],
                    "pdf_count": doc_analysis["pdf_docs_count"],
                    "excel_count": doc_analysis["excel_docs_count"],
                    "doc_count": doc_analysis["doc_docs_count"],
                    "time_ms": retrieval_time_ms
                },
                
                "context": {
                    "size": {
                        "chars": context_size_chars,
                        "tokens": context_size_tokens,
                        "chunks": len(final_docs)
                    },
                    "preparation_ms": retrieval_time_ms,
                    "truncated": len(unique_docs) > 30,
                    "conversation": {
                        "has_history": bool(conversation_context),
                        "turns": len(conversation_context.split("\n")) if conversation_context else 0,
                        "size_chars": len(conversation_context) if conversation_context else 0
                    }
                },
                
                # ===== CONTEXT STRING FOR LLM-AS-A-JUDGE EVALUATION =====
                # This field is used by Langfuse evaluators to assess response quality
                "context_string": "\n\n=== DOCUMENT ===\n\n".join([
                    doc.page_content for doc in final_docs[:10]  # Top 10 most relevant docs
                ]),
                
                "generation": {
                    "model": "gpt-4o-mini",
                    "config": {
                        "temperature": 0.3,
                        "max_tokens": 1500,
                        "streaming": True
                    },
                    "response": {
                        "length_words": len(full_response.split()),
                        "length_chars": len(full_response)
                    },
                    "time_ms": llm_time_ms
                },
                
                "performance": {
                    "total_ms": total_time_ms,
                    "breakdown": {
                        "retrieval_ms": retrieval_time_ms,
                        "llm_ms": llm_time_ms,
                        "thinking_ms": thinking_time_ms,
                        "streaming_ms": streaming_time_ms
                    }
                },
                
                "system": {
                    "vectorstore_available": vectorstore is not None,
                    "documents_found": len(final_docs) > 0,
                    "vectorstore_version": get_vectorstore_build_date()
                }
            }
            
            # ===== COMPLETE RAG PIPELINE TRACE =====
            trace_id = None
            try:
                if rag_trace:
                    # Log LLM generation
                    rag_trace.log_llm_generation(
                        prompt=str(messages),
                        response=full_response,
                        model="gpt-4o-mini",
                        metadata={
                            "temperature": 0.3,
                            "max_tokens": 1500,
                            "response_length": len(full_response)
                        }
                    )
                    
                    # Log final response generation
                    rag_trace.log_response_generation(
                        final_response=full_response,
                        metadata={
                            **comprehensive_metadata,
                            "sources_used": sources_used if sources_used else [],
                        }
                    )
                    
                    # Complete the trace with comprehensive metadata
                    trace_id = rag_trace.complete(full_response, metadata=comprehensive_metadata)
                else:
                    # Fallback to simple trace if RAG trace failed
                    trace_id = langfuse_tracker.create_trace(
                        user_id=conversation_id,
                        question=question,
                        answer=full_response,
                        session_id=session_id,
                        user_name=user_name,
                        user_email=user_email,
                        metadata=comprehensive_metadata
                    )
            except Exception as e:
                print(f"[WARNING] Langfuse logging failed: {e}")
            
            # Send completion signal with trace_id
            yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'trace_id': trace_id})}\n\n"
            
        except Exception as e:
            print(f"[ERROR] ERROR in generate_stream: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

# ---------------- User Chat History Endpoints ----------------

@router.get("/chat/history/{user_id}")
async def get_chat_history(
    user_id: str,
    current_user: dict = Depends(verify_user_access)
):
    """Get chat history for authenticated user only. Protected against IDOR."""
    try:
        history = await get_user_chat_history(user_id)
        return {"user_id": user_id, "history": history}
    except Exception as e:
        return {"error": str(e)}

@router.delete("/chat/history/{user_id}")
async def clear_chat_history(
    user_id: str,
    current_user: dict = Depends(verify_user_access)
):
    """Clear chat history for authenticated user only. Protected against IDOR."""
    try:
        await clear_user_chat_history(user_id)
        return {"message": f"Chat history cleared for user {user_id}"}
    except Exception as e:
        return {"error": str(e)}

# ---------------- Feedback Endpoint ----------------

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback (👍/👎) for a chat interaction."""
    try:
        # Validate rating
        if request.rating not in ["thumbs_up", "thumbs_down"]:
            return {"error": "Invalid rating. Must be 'thumbs_up' or 'thumbs_down'"}
        
        # Log feedback to Langfuse
        success = langfuse_tracker.add_feedback(
            trace_id=request.trace_id,
            rating=request.rating,
            comment=request.comment
        )
        
        # COMMENTED OUT: Auto-correction workflow (now using manual correction)
        # await track_feedback_history(request.trace_id, request.rating, request.comment)
        # 
        # # If thumbs down, trigger auto-correction immediately
        # if request.rating == "thumbs_down":
        #     try:
        #         # Get the original question and response from the trace
        #         original_data = await get_trace_data(request.trace_id)
        #         if original_data:
        #             # Trigger auto-correction
        #             corrected_response = await trigger_auto_correction_workflow(
        #                 trace_id=request.trace_id,
        #                 user_query=original_data.get("question", ""),
        #                 bad_response=original_data.get("response", ""),
        #                 user_comment=request.comment
        #             )
        #     except Exception as e:
        #         print(f"Auto-correction failed: {e}")
        
        if success:
            return {
                "status": "success",
                "message": "Feedback recorded successfully",
                "trace_id": request.trace_id,
                "auto_correction_triggered": False  # Manual correction will be used instead
            }
        else:
            return {
                "status": "error",
                "message": "Failed to record feedback"
            }
            
    except Exception as e:
        return {"error": f"Failed to submit feedback: {str(e)}"}

# ---------------- Auto-Correction System ----------------

async def track_feedback_history(trace_id: str, rating: str, comment: str = None):
    """Track feedback history for smart auto-correction decisions."""
    try:
        feedback_file = "./data/feedback_history.json"
        
        # Load existing data
        if os.path.exists(feedback_file):
            with open(feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"feedback_history": {}}
        
        # Initialize trace data if not exists
        if trace_id not in data["feedback_history"]:
            data["feedback_history"][trace_id] = {
                "negative_count": 0,
                "positive_count": 0,
                "total_count": 0,
                "question_asked_before": False,
                "feedback_history": []
            }
        
        # Update counts
        trace_data = data["feedback_history"][trace_id]
        trace_data["total_count"] += 1
        
        if rating == "thumbs_down":
            trace_data["negative_count"] += 1
        else:
            trace_data["positive_count"] += 1
        
        # Add to feedback history
        feedback_entry = {
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }
        trace_data["feedback_history"].append(feedback_entry)
        
        # Save updated data
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        print(f"Error tracking feedback history: {e}")

async def should_trigger_auto_correction(trace_id: str, user_comment: str = None) -> bool:
    """Simplified auto-correction logic - more effective and predictable."""
    try:
        # Load feedback history
        feedback_stats = await get_feedback_stats_for_question(trace_id)
        negative_count = feedback_stats.get('negative_count', 0)
        
        # SIMPLIFIED RULES - More predictable and effective
        
        # Rule 1: Always correct if user provides specific feedback
        if user_comment and len(user_comment.strip()) > 15:
            return True
        
        # Rule 2: Correct if 2+ negative feedbacks (simple threshold)
        if negative_count >= 2:
            return True
        
        # Rule 3: Correct if this is a recurring problem (same question, multiple negatives)
        if negative_count >= 1 and feedback_stats.get('question_asked_before', False):
            return True
        
        # Rule 4: Don't correct for single negative feedback
        return False
            
    except Exception as e:
        print(f"Error in auto-correction logic: {e}")
        return False

async def get_feedback_stats_for_question(trace_id: str) -> dict:
    """Get feedback statistics for a question to make smart decisions."""
    try:
        # In a real implementation, you'd query Langfuse API for feedback history
        # For now, we'll simulate with local data
        
        # Check if we have feedback data for this trace
        feedback_file = "./data/feedback_history.json"
        
        if os.path.exists(feedback_file):
            with open(feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Find feedback for this trace
            trace_feedback = data.get('feedback_history', {}).get(trace_id, {})
            return trace_feedback
        else:
            # No history, treat as first time
            return {
                'negative_count': 0,
                'total_count': 0,
                'question_asked_before': False
            }
            
    except Exception as e:
        print(f"Error getting feedback stats: {e}")
        return {
            'negative_count': 0,
            'total_count': 0,
            'question_asked_before': False
        }

async def trigger_auto_correction(trace_id: str, user_comment: str = None):
    """Trigger auto-correction for a thumbs down feedback."""
    try:
        # Get the original trace data from Langfuse
        # For now, we'll simulate getting the original question and answer
        # In a real implementation, you'd fetch this from Langfuse API
        
        # Create auto-correction prompt
        correction_prompt = f"""
        The user gave negative feedback (👎) on this response. Please provide a better, improved version.
        
        Original question: [QUESTION_PLACEHOLDER]
        Original answer: [ANSWER_PLACEHOLDER]
        User feedback: {user_comment or "User indicated the response was not helpful"}
        
        Please provide an improved response that:
        1. Directly addresses the user's question
        2. Is more helpful and accurate
        3. Provides specific, actionable information
        4. Is clear and well-structured
        
        Improved response:
        """
        
        # Use LLM to generate improved response
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.3)
        
        # For now, we'll create a generic improved response
        # In a real implementation, you'd fetch the original Q&A from Langfuse
        improved_response = await generate_improved_response(correction_prompt, llm)
        
        # Save to dataset
        # Note: This doesn't have the original question - would need Langfuse integration to get it
        save_corrected_response(trace_id, improved_response, user_comment, None)
        
    except Exception as e:
        print(f"Auto-correction failed: {e}")
        raise e

async def generate_improved_response(prompt: str, llm):
    """Generate an improved response using LLM."""
    try:
        # Create a simple prompt template
        template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert AI assistant. Improve the given response to be more helpful and accurate."),
            ("human", "{prompt}")
        ])
        
        chain = template | llm
        result = await chain.ainvoke({"prompt": prompt})
        return result.content
        
    except Exception as e:
        print(f"Error generating improved response: {e}")
        return "I apologize, but I'm having trouble generating an improved response at the moment."

def save_corrected_response(trace_id: str, corrected_response: str, user_comment: str = None, original_question: str = None):
    """Save the corrected response to the dataset."""
    try:
        # Create dataset directory if it doesn't exist
        dataset_dir = "./data/corrected_responses"
        os.makedirs(dataset_dir, exist_ok=True)
        
        # Create dataset entry
        dataset_entry = {
            "trace_id": trace_id,
            "corrected_response": corrected_response,
            "original_question": original_question,  # Store the original question for similarity matching
            "user_comment": user_comment,
            "timestamp": datetime.now().isoformat(),
            "status": "corrected"
        }
        
        # Save to JSON file
        dataset_file = f"{dataset_dir}/corrected_responses.json"
        
        # Load existing data
        if os.path.exists(dataset_file):
            with open(dataset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"corrected_responses": []}
        
        # Add new entry
        data["corrected_responses"].append(dataset_entry)
        
        # Save back to file
        with open(dataset_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        print(f"Error saving corrected response: {e}")

@router.get("/dataset/corrected-responses")
async def get_corrected_responses(current_user: dict = Depends(require_admin)):
    """Get all corrected responses from the dataset. Requires admin access."""
    try:
        dataset_file = "./data/corrected_responses/corrected_responses.json"
        
        if not os.path.exists(dataset_file):
            return {"corrected_responses": [], "count": 0}
        
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "corrected_responses": data.get("corrected_responses", []),
            "count": len(data.get("corrected_responses", []))
        }
        
    except Exception as e:
        return {"error": f"Failed to load corrected responses: {str(e)}"}

@router.delete("/dataset/corrected-responses")
async def clear_corrected_responses(current_user: dict = Depends(require_admin)):
    """Clear all corrected responses from the dataset. Requires admin access."""
    try:
        dataset_file = "./data/corrected_responses/corrected_responses.json"
        
        if os.path.exists(dataset_file):
            os.remove(dataset_file)
            return {"message": "Corrected responses dataset cleared"}
        else:
            return {"message": "No dataset found to clear"}
            
    except Exception as e:
        return {"error": f"Failed to clear dataset: {str(e)}"}

# ---------------- Manual Fine-Tuning System ----------------

@router.post("/fine-tuning/trigger")
async def trigger_manual_fine_tuning(current_user: dict = Depends(require_admin)):
    """Manually trigger fine-tuning when needed. Requires admin access."""
    try:
        # Check if we have enough data for fine-tuning
        dataset_status = await check_dataset_quality()
        
        if not dataset_status["ready_for_training"]:
            return {
                "status": "insufficient_data",
                "message": f"Not enough data for fine-tuning. Need at least {dataset_status['min_required']} samples, have {dataset_status['current_count']}",
                "recommendations": dataset_status["recommendations"]
            }
        
        # Start fine-tuning process
        fine_tuning_result = await start_fine_tuning_process()
        
        return {
            "status": "success",
            "message": "Fine-tuning process started",
            "dataset_info": dataset_status,
            "process_id": fine_tuning_result["process_id"]
        }
        
    except Exception as e:
        return {"error": f"Failed to trigger fine-tuning: {str(e)}"}

@router.get("/fine-tuning/status")
async def get_fine_tuning_status(current_user: dict = Depends(require_admin)):
    """Get the status of fine-tuning process. Requires admin access."""
    try:
        # Check dataset quality
        dataset_status = await check_dataset_quality()
        
        # Check if fine-tuning is in progress
        training_status = await get_training_status()
        
        return {
            "dataset_quality": dataset_status,
            "training_status": training_status,
            "recommendations": await get_fine_tuning_recommendations()
        }
        
    except Exception as e:
        return {"error": f"Failed to get fine-tuning status: {str(e)}"}

async def check_dataset_quality():
    """Check if dataset is ready for fine-tuning."""
    try:
        dataset_file = "./data/corrected_responses/corrected_responses.json"
        
        if not os.path.exists(dataset_file):
            return {
                "ready_for_training": False,
                "current_count": 0,
                "min_required": 10,
                "recommendations": ["Collect more negative feedback data"]
            }
        
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        corrected_responses = data.get("corrected_responses", [])
        current_count = len(corrected_responses)
        min_required = 10  # Minimum samples needed
        
        # Quality checks
        quality_score = 0
        recommendations = []
        
        if current_count >= min_required:
            quality_score += 40
        else:
            recommendations.append(f"Need {min_required - current_count} more samples")
        
        # Check for diverse feedback
        unique_questions = len(set([item.get("original_question", "") for item in corrected_responses]))
        if unique_questions >= 5:
            quality_score += 30
        else:
            recommendations.append("Need more diverse question types")
        
        # Check for recent data
        recent_count = 0
        for item in corrected_responses:
            timestamp = datetime.fromisoformat(item.get("timestamp", ""))
            if (datetime.now() - timestamp).days <= 7:
                recent_count += 1
        
        if recent_count >= 3:
            quality_score += 30
        else:
            recommendations.append("Need more recent feedback data")
        
        return {
            "ready_for_training": quality_score >= 70,
            "current_count": current_count,
            "min_required": min_required,
            "quality_score": quality_score,
            "unique_questions": unique_questions,
            "recent_samples": recent_count,
            "recommendations": recommendations
        }
        
    except Exception as e:
        return {
            "ready_for_training": False,
            "error": str(e),
            "recommendations": ["Fix dataset issues"]
        }

async def start_fine_tuning_process():
    """Start the fine-tuning process."""
    try:
        # Generate a unique process ID
        process_id = f"ft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # In a real implementation, you would:
        # 1. Export data from Langfuse
        # 2. Prepare training data
        # 3. Start fine-tuning job
        # 4. Monitor progress
        
        # For now, simulate the process
        training_status = {
            "process_id": process_id,
            "status": "started",
            "start_time": datetime.now().isoformat(),
            "estimated_completion": (datetime.now().timestamp() + 3600),  # 1 hour from now
            "progress": 0
        }
        
        # Save training status
        status_file = "./data/fine_tuning_status.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(training_status, f, indent=2, ensure_ascii=False)
        
        return training_status
        
    except Exception as e:
        print(f"Failed to start fine-tuning: {e}")
        raise e

async def get_training_status():
    """Get current training status."""
    try:
        status_file = "./data/fine_tuning_status.json"
        
        if not os.path.exists(status_file):
            return {"status": "no_training", "message": "No fine-tuning in progress"}
        
        with open(status_file, 'r', encoding='utf-8') as f:
            status = json.load(f)
        
        return status
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_fine_tuning_recommendations():
    """Get recommendations for when to run fine-tuning."""
    try:
        dataset_status = await check_dataset_quality()
        
        recommendations = []
        
        if not dataset_status["ready_for_training"]:
            recommendations.append("[FAIL] Not ready for fine-tuning - insufficient data")
            recommendations.extend(dataset_status["recommendations"])
        else:
            recommendations.append("[OK] Ready for fine-tuning!")
            recommendations.append("Consider running fine-tuning when you have 20+ samples")
            recommendations.append("Run fine-tuning weekly for best results")
        
        return recommendations
        
    except Exception as e:
        return [f"Error getting recommendations: {str(e)}"]

# ---------------- Auto-Correction Workflow ----------------

async def get_trace_data(trace_id: str):
    """Get original question and response from trace data."""
    try:
        # In a real implementation, you would retrieve this from Langfuse
        # For now, we'll simulate it
        return {
            "question": "Sample question from trace",
            "response": "Sample response from trace"
        }
    except Exception as e:
        print(f"Error retrieving trace data: {e}")
        return None

async def trigger_auto_correction_workflow(trace_id: str, user_query: str, bad_response: str, user_comment: str = None):
    """Complete auto-correction workflow."""
    try:
        # Step 1: Generate improved response using LLM
        improved_response = await generate_improved_response(user_query, bad_response, user_comment)
        
        # Step 2: Save to correction dataset
        await save_correction_to_dataset(user_query, bad_response, improved_response, trace_id, user_comment)
        
        # Step 3: Update Langfuse trace (optional)
        await update_langfuse_trace(trace_id, improved_response)
        
        return improved_response
        
    except Exception as e:
        print(f"Auto-correction workflow failed: {e}")
        raise e

async def generate_improved_response(user_query: str, bad_response: str, user_comment: str = None):
    """Use LLM with RAG to generate an improved response using the knowledge base."""
    try:
        from langchain_openai import ChatOpenAI
        
        # CRITICAL: Retrieve relevant documents from vectorstore for context
        # This ensures the corrected response is based on actual knowledge base
        if vectorstore is None:
            print("Warning: Vectorstore not initialized. Cannot retrieve context for improved response.")
            relevant_docs = []
        else:
            relevant_docs = vectorstore.similarity_search(user_query, k=25)
        
        # Build debug info for context
        context_debug_info = {
            "doc_count": len(relevant_docs),
            "query": user_query,
            "docs": [
                {
                    "doc_number": i + 1,
                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "content_length": len(doc.page_content),
                    "metadata": doc.metadata,
                    "source": doc.metadata.get('source', 'Unknown')
                }
                for i, doc in enumerate(relevant_docs[:10])  # Save first 10 docs for review
            ]
        }
        
        # Format the retrieved documents as context
        context_text = "\n\n".join([f"Document {i+1}:\n{doc.page_content}" for i, doc in enumerate(relevant_docs)])
        
        # Create LLM for auto-correction
        llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.5,
            max_tokens=1000
        )
        
        # Create auto-correction prompt WITH knowledge base context
        correction_prompt = f"""
{SYSTEM_PROMPT}

ADDITIONAL CONTEXT FOR CORRECTION:

KNOWLEDGE BASE CONTEXT:
{context_text}

PREVIOUS INTERACTION:
User's Question: "{user_query}"
Bot's Poor Response: "{bad_response}"
{f"User's Feedback: {user_comment}" if user_comment else ""}

CORRECTION TASK:
The previous response was marked as poor quality. Using ONLY the information from the KNOWLEDGE BASE CONTEXT above, provide a much better, more accurate, and helpful response that:

1. Follows ALL the instructions from the system prompt at the top (including link embedding and markdown formatting)
2. Directly answers the user's question about cloud migration services
3. Uses specific information from the knowledge base documents
4. Provides actionable information about CloudFuze's capabilities
5. Is clear, professional, and helpful
6. Includes relevant CloudFuze links.
7. Uses proper Markdown formatting as specified in the system prompt
8. Concludes with a helpful suggestion to contact CloudFuze with the contact link

CRITICAL RULES:
- Base your answer STRICTLY on the knowledge base context provided above
- Use the EXACT same style, tone, and formatting as the system prompt requires
- Include relevant CloudFuze links naturally in the response
- DO NOT invent information not in the knowledge base context
- If information is not in the context, say "I don't have specific information about that and  Concludes with a helpful suggestion to contact CloudFuze with the contact link"

Improved response:
"""
        
        # Generate improved response with knowledge base context
        improved_response = (await llm.ainvoke(correction_prompt)).content
        
        # Return both the response and context debug info
        return improved_response, context_debug_info
        
    except Exception as e:
        print(f"Error generating improved response: {e}")
        error_response = f"I apologize for the previous response. Let me provide a better answer to your question: {user_query}. For detailed information about Slack to Teams migration, please contact our CloudFuze support team."
        return error_response, {"error": str(e), "doc_count": 0}

async def save_correction_to_dataset(user_query: str, bad_response: str, improved_response: str, trace_id: str, user_comment: str = None):
    """Save the correction to JSONL dataset."""
    try:
        import os
        from datetime import datetime
        
        # Create dataset directory if it doesn't exist
        dataset_dir = "./data/fine_tuning_dataset"
        os.makedirs(dataset_dir, exist_ok=True)
        
        # Create JSONL record
        correction_record = {
            "input": user_query,
            "bad_output": bad_response,
            "corrected_output": improved_response,
            "trace_id": trace_id,
            "user_comment": user_comment,
            "timestamp": datetime.now().isoformat(),
            "status": "auto_corrected"
        }
        
        # Save to single JSONL file (append mode)
        jsonl_file = f"{dataset_dir}/corrections.jsonl"
        
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(correction_record, ensure_ascii=False) + '\n')
        
        # Also save to the existing corrected_responses.json for compatibility
        # Pass the original question so similarity matching can work
        save_corrected_response(trace_id, improved_response, user_comment, user_query)
        
    except Exception as e:
        print(f"Error saving correction to dataset: {e}")

async def update_langfuse_trace(trace_id: str, improved_response: str):
    """Update Langfuse trace with corrected response."""
    try:
        if langfuse_tracker and langfuse_tracker.client:
            # Log the auto-correction as a score/annotation
            langfuse_tracker.client.score(
                trace_id=trace_id,
                name="auto_correction",
                value=1,
                comment=f"Auto-corrected response: {improved_response[:200]}..."
            )
    except Exception as e:
        print(f"Could not update Langfuse trace: {e}")

# ---------------- Microsoft OAuth Endpoints ----------------

class MicrosoftCallbackRequest(BaseModel):
    code: str
    redirect_uri: str
    code_verifier: str

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify backend connectivity."""
    return {"message": "Backend is working", "status": "success"}

@router.get("/auth/config")
async def get_auth_config():
    """Get OAuth configuration for frontend."""
    return {
        "client_id": MICROSOFT_CLIENT_ID,
        "tenant": MICROSOFT_TENANT
    }

@router.post("/test-post")
async def test_post_endpoint(data: dict):
    """Test POST endpoint to verify CORS and connectivity."""
    return {"message": "POST request received", "data": data, "status": "success"}

@router.post("/auth/microsoft/callback")
async def microsoft_oauth_callback(request: MicrosoftCallbackRequest):
    """Handle Microsoft OAuth callback and exchange code for tokens."""
    try:
        # Get Microsoft OAuth configuration
        client_id = MICROSOFT_CLIENT_ID
        tenant = MICROSOFT_TENANT
        
        # Exchange authorization code for access token
        token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        
        # For confidential clients (Web apps), we use client_secret
        token_data = {
            "client_id": client_id,
            "client_secret": MICROSOFT_CLIENT_SECRET,
            "code": request.code,
            "redirect_uri": request.redirect_uri,
            "code_verifier": request.code_verifier,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            
            if token_response.status_code != 200:
                return {"error": "Failed to exchange code for token", "details": token_response.text}
            
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            
            if not access_token:
                return {"error": "No access token received"}
            
            # Get user information from Microsoft Graph
            graph_response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if graph_response.status_code != 200:
                return {"error": "Failed to get user information", "details": graph_response.text}
            
            user_info = graph_response.json()
            
            # Create user ID from Microsoft user ID
            user_id = user_info.get("id")
            user_name = user_info.get("displayName", "User")
            user_email = user_info.get("mail") or user_info.get("userPrincipalName", "")
            
            # Validate that the user has a CloudFuze email domain
            if not user_email.endswith("@cloudfuze.com"):
                return {
                    "error": "Access denied", 
                    "message": "Only CloudFuze company accounts are allowed to access this application.",
                    "details": f"Email domain not allowed: {user_email}"
                }
            
            result = {
                "user_id": user_id,
                "name": user_name,
                "email": user_email,
                "access_token": access_token,
                "refresh_token": token_info.get("refresh_token", "")
            }
            
            return result
            
    except Exception as e:
        return {"error": f"OAuth callback failed: {str(e)}"}
