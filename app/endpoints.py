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
from app.vectorstore import retriever, vectorstore, bm25_retriever
from app.mongodb_memory import add_to_conversation, get_conversation_context, get_user_chat_history, clear_user_chat_history
from app.helpers import strip_markdown, preserve_markdown
from app.langfuse_integration import langfuse_tracker
from app.auth import verify_user_access, require_admin
from config import (
    SYSTEM_PROMPT, MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_TENANT,
    ENABLE_INTENT_CLASSIFICATION, ENABLE_QUERY_EXPANSION, ENABLE_CONTEXT_COMPRESSION,
    DENSE_RETRIEVAL_K, BM25_RETRIEVAL_K, FINAL_RETRIEVAL_K,
    DENSE_WEIGHT, BM25_WEIGHT, RERANKER_WEIGHT
)
from langchain_core.prompts import ChatPromptTemplate
import time
from query_expander import QueryExpander
from reranker import CrossEncoderReranker
from context_compressor import ContextCompressor
from contextlib import suppress


# ============================================================================
# OPTION E: PERPLEXITY-STYLE RETRIEVAL INITIALIZATION
# ============================================================================

# Initialize Option E components
query_expander = QueryExpander()
cross_reranker = CrossEncoderReranker()
context_compressor = ContextCompressor()

# ============================================================================
# INTENT CLASSIFICATION SYSTEM - Branch-Specific Retrieval
# ============================================================================

# Configuration: Disable intent classification (overridden by config)
# ENABLE_INTENT_CLASSIFICATION is now imported from config

# Define intent branches with their characteristics
INTENT_BRANCHES = {
    "general_business": {
        "description": "General business questions, CloudFuze overview, benefits",
        "keywords": ["business", "help", "benefits", "useful", "value", "cloudfuze", "services", "offer", "advantages"],
        "include_tags": ["blog"],
        "exclude_keywords": ["slack", "teams", "migration", "migrate"],
        "exclude_if_both": [("slack", "teams")],
        "query_expansion": ["cloud solutions", "data migration platform", "SaaS management"]
    },
    "slack_teams_migration": {
        "description": "Slack to Teams migration specific questions",
        "keywords": ["slack", "teams", "slack to teams", "migrate slack", "migration"],
        "include_tags": ["blog", "sharepoint"],
        "require_keywords": [["slack", "teams"], ["slack-to-teams"]],
        "query_expansion": ["channel migration", "workspace transfer", "conversation history"]
    },
    "sharepoint_docs": {
        "description": "SharePoint documents, certificates, policies",
        "keywords": ["certificate", "download", "policy", "document", "soc", "compliance", "security"],
        "include_tags": ["sharepoint"],
        "priority_source": "sharepoint",
        "query_expansion": ["compliance documentation", "security certification", "audit reports"]
    },
    "pricing": {
        "description": "Pricing, costs, payment questions",
        "keywords": ["pricing", "cost", "price", "how much", "payment", "subscription", "plan"],
        "include_tags": ["blog"],
        "query_expansion": ["subscription plans", "licensing", "payment options"]
    },
    "troubleshooting": {
        "description": "Errors, issues, stuck migrations",
        "keywords": ["error", "stuck", "not working", "failed", "issue", "problem", "fix"],
        "include_tags": ["blog", "sharepoint"],
        "query_expansion": ["error resolution", "migration issues", "technical support"]
    },
    "migration_general": {
        "description": "General migration questions (not platform-specific)",
        "keywords": ["migrate", "migration", "transfer", "move data", "cloud migration"],
        "include_tags": ["blog", "sharepoint"],
        "exclude_if_both": [("slack", "teams")],
        "query_expansion": ["data transfer", "cloud-to-cloud migration", "platform migration"]
    },
    "enterprise_solutions": {
        "description": "Enterprise features, large-scale deployments",
        "keywords": ["enterprise", "large scale", "organization", "corporate", "enterprise-grade"],
        "include_tags": ["blog", "sharepoint"],
        "query_expansion": ["enterprise deployment", "large organization", "corporate solutions"]
    },
    "integrations": {
        "description": "API, integrations, third-party connections",
        "keywords": ["api", "integration", "webhook", "connector", "third-party", "integrate with"],
        "include_tags": ["blog", "sharepoint"],
        "query_expansion": ["API integration", "third-party connectors", "platform connectivity"]
    },
    "features": {
        "description": "Product features and capabilities",
        "keywords": ["features", "capabilities", "what can", "functionality", "does it support"],
        "include_tags": ["blog", "sharepoint"],
        "query_expansion": ["product capabilities", "feature list", "platform features"]
    },
    "email_conversations": {
        "description": "Questions about email threads, conversations, and discussions",
        "keywords": ["email", "thread", "conversation", "discussed", "bugs", "participants", "srcs", "what did", "who said"],
        "include_tags": ["email"],
        "query_expansion": ["email thread", "conversation", "discussion"]
    },
    "other": {
        "description": "Fallback for uncategorized queries",
        "keywords": [],
        "include_tags": ["blog", "sharepoint", "email"],
        "query_expansion": []
    }
}


def classify_intent(query: str) -> dict:
    """
    Classify user query intent using LLM-based classification.
    Returns intent name and confidence score.
    """
    from langchain_openai import ChatOpenAI
    
    query_lower = query.lower()
    
    # Quick keyword-based pre-filter for common cases (faster)
    if any(kw in query_lower for kw in ["email", "thread", "conversation", "bugs raised", "discussed", "srcs folder", "participants"]):
        return {"intent": "email_conversations", "confidence": 0.90, "method": "keyword"}
    
    if any(kw in query_lower for kw in ["certificate", "download", "soc", "policy"]) and "sharepoint" not in query_lower:
        if any(word in query_lower for word in ["certificate", "compliance", "security", "policy"]):
            return {"intent": "sharepoint_docs", "confidence": 0.85, "method": "keyword"}
    
    if "slack" in query_lower and "teams" in query_lower:
        return {"intent": "slack_teams_migration", "confidence": 0.90, "method": "keyword"}
    
    if any(kw in query_lower for kw in ["pricing", "cost", "price", "how much"]):
        return {"intent": "pricing", "confidence": 0.85, "method": "keyword"}
    
    # For ambiguous queries, use LLM classification
    intent_descriptions = "\n".join([f"{i+1}. {key}: {config['description']}" 
                                     for i, (key, config) in enumerate(INTENT_BRANCHES.items())])
    
    classifier_prompt = f"""Classify this user query into ONE of these intents:

{intent_descriptions}

Query: "{query}"

CRITICAL RULES:
- If query asks about emails, conversations, threads, or discusses what was said in emails → "email_conversations"
- If query asks about general business value, benefits, or "what is CloudFuze" WITHOUT mentioning specific platforms → "general_business"
- If query mentions BOTH "Slack" AND "Teams" → "slack_teams_migration"
- If query asks about general migration (without specific platforms) → "migration_general"
- If query asks for certificates, documents, or policies → "sharepoint_docs"
- If query asks about pricing or costs → "pricing"
- If query describes errors or problems → "troubleshooting"
- If query asks about enterprise features or large-scale → "enterprise_solutions"
- If query asks about API, integrations, or connectors → "integrations"
- If query asks about features or capabilities → "features"
- Otherwise → "other"

Respond with EXACTLY this format (no extra text):
intent_name|confidence

Example: general_business|0.92
"""
    
    try:
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
        response = llm.invoke(classifier_prompt)
        
        parts = response.content.strip().split('|')
        intent = parts[0].strip()
        confidence = float(parts[1].strip()) if len(parts) > 1 else 0.7
        
        # Validate intent exists
        if intent not in INTENT_BRANCHES:
            intent = "other"
            confidence = 0.5
        
        return {
            "intent": intent,
            "confidence": confidence,
            "method": "llm"
        }
    except Exception as e:
        print(f"[ERROR] Intent classification failed: {e}")
        return {"intent": "other", "confidence": 0.5, "method": "fallback"}


def retrieve_with_branch_filter(query: str, intent: str, k: int = 50):
    """
    Retrieve documents filtered by intent branch.
    This performs semantic search and then filters by metadata tags.
    """
    branch_config = INTENT_BRANCHES.get(intent, INTENT_BRANCHES["other"])
    
    # Get more documents than needed for filtering
    all_docs = vectorstore.similarity_search_with_score(query, k=100)
    
    filtered_docs = []
    
    for doc, score in all_docs:
        doc_tag = doc.metadata.get('tag', '').lower()
        doc_content = doc.page_content.lower()
        doc_title = doc.metadata.get('post_title', '').lower()
        source_type = doc.metadata.get('source_type', '').lower()
        
        # Check inclusion tags
        include_tags = branch_config.get("include_tags", [])
        if include_tags:
            tag_match = any(tag in doc_tag for tag in include_tags)
        else:
            tag_match = True
        
        # For general_business intent: exclude Slack→Teams specific content
        if intent == "general_business":
            # Check if document is Slack→Teams specific
            exclude_keywords = branch_config.get("exclude_keywords", [])
            has_excluded = False
            
            # Strong exclusion: if both "slack" and "teams" appear multiple times
            slack_count = doc_content.count("slack")
            teams_count = doc_content.count("teams")
            if slack_count >= 2 and teams_count >= 2:
                has_excluded = True
            
            # Title-based exclusion
            if "slack to teams" in doc_title or "slack-to-teams" in doc_title:
                has_excluded = True
            
            if has_excluded:
                continue  # Skip this document
        
        # For slack_teams_migration: prioritize relevant content
        elif intent == "slack_teams_migration":
            # Must have both slack and teams keywords
            if "slack" not in doc_content and "slack" not in doc_title:
                tag_match = False
            if "teams" not in doc_content and "teams" not in doc_title:
                tag_match = False
        
        # For sharepoint_docs: prioritize SharePoint source
        elif intent == "sharepoint_docs":
            if source_type == "sharepoint":
                # Boost SharePoint docs by improving their score
                score = score * 0.7  # Lower score = higher priority
        
        # Add document if it passes filters
        if tag_match:
            filtered_docs.append((doc, score))
    
    # Sort by score (lower is better in similarity search)
    filtered_docs.sort(key=lambda x: x[1])
    
    # Return top k
    return filtered_docs[:k]


def calculate_confidence(intent_confidence: float, retrieval_docs: int, avg_similarity: float = None):
    """
    Calculate overall confidence score for the response.
    Combines intent classification confidence with retrieval metrics.
    """
    # Intent confidence weight: 50%
    # Document count weight: 30%
    # Similarity weight: 20%
    
    # Normalize document count (30 is ideal)
    doc_confidence = min(retrieval_docs / 30.0, 1.0)
    
    if avg_similarity is not None:
        # Similarity scores are distances (lower is better), typically 0.3-0.6
        # Convert to confidence: 0.3 → 0.95, 0.6 → 0.4
        similarity_confidence = max(0, 1.0 - avg_similarity)
        
        overall_confidence = (
            intent_confidence * 0.5 +
            doc_confidence * 0.3 +
            similarity_confidence * 0.2
        )
    else:
        overall_confidence = (
            intent_confidence * 0.6 +
            doc_confidence * 0.4
        )
    
    return round(overall_confidence, 3)


# ============================================================================
# ADVANCED RAG IMPROVEMENTS
# ============================================================================

def expand_query_with_intent(query: str, intent: str) -> str:
    """
    Expand query with intent-specific keywords for better retrieval.
    Uses query expansion terms defined in intent branches.
    """
    branch_config = INTENT_BRANCHES.get(intent, {})
    expansion_terms = branch_config.get("query_expansion", [])
    
    if not expansion_terms:
        return query
    
    # Add expansion terms to original query
    expanded = f"{query} {' '.join(expansion_terms[:2])}"  # Add top 2 terms
    
    print(f"[QUERY EXPANSION] Original: '{query}' → Expanded: '{expanded}'")
    
    return expanded


def hybrid_ranking(doc_results, query: str, intent: str, alpha=0.7):
    """
    Hybrid ranking combining semantic similarity + keyword matching.
    alpha: weight for semantic score (1-alpha for keyword score)
    """
    from collections import Counter
    import re
    
    # Get keywords from intent branch
    branch_config = INTENT_BRANCHES.get(intent, {})
    intent_keywords = branch_config.get("keywords", [])
    
    # Extract keywords from query
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    reranked_docs = []
    
    for doc, semantic_score in doc_results:
        # Semantic score (already normalized, lower is better)
        semantic_component = semantic_score
        
        # Keyword matching score
        doc_text = doc.page_content.lower()
        doc_title = doc.metadata.get('post_title', '').lower()
        
        # Count keyword matches
        keyword_matches = 0
        for keyword in query_words:
            if len(keyword) > 3:  # Skip short words
                keyword_matches += doc_text.count(keyword)
                keyword_matches += doc_title.count(keyword) * 2  # Title matches count more
        
        # Count intent keyword matches
        for intent_kw in intent_keywords:
            if intent_kw in doc_text:
                keyword_matches += 1
        
        # Normalize keyword score (inverse, so lower is better like semantic)
        keyword_score = max(0, 1.0 - (keyword_matches / 20.0))  # Normalize to 0-1
        
        # Hybrid score (lower is better)
        hybrid_score = (alpha * semantic_component) + ((1 - alpha) * keyword_score)
        
        reranked_docs.append((doc, hybrid_score, {
            "semantic": semantic_component,
            "keyword": keyword_score,
            "keyword_matches": keyword_matches
        }))
    
    # Sort by hybrid score
    reranked_docs.sort(key=lambda x: x[1])
    
    # Return in original format (doc, score)
    return [(doc, score) for doc, score, _ in reranked_docs]


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


def confidence_based_fallback(doc_results, intent: str, intent_confidence: float, query: str):
    """
    If confidence is low, try fallback retrieval strategies.
    Returns enhanced doc_results or original if fallback not needed.
    """
    # If confidence is already high, no fallback needed
    if intent_confidence >= 0.75:
        return doc_results, "no_fallback"
    
    print(f"[FALLBACK] Low confidence ({intent_confidence:.2f}), trying fallback strategies...")
    
    # Strategy 1: Try with "other" intent (broader search)
    if intent != "other" and intent_confidence < 0.6:
        print(f"[FALLBACK] Strategy 1: Expanding to 'other' branch")
        fallback_docs = retrieve_with_branch_filter(query, "other", k=50)
        
        # Merge with original results (deduplicate)
        seen = set()
        merged = []
        
        for doc, score in doc_results + fallback_docs:
            doc_id = f"{doc.metadata.get('source', '')}_{doc.page_content[:100]}"
            if doc_id not in seen:
                seen.add(doc_id)
                merged.append((doc, score))
        
        # Re-sort and limit
        merged.sort(key=lambda x: x[1])
        return merged[:50], "fallback_other_branch"
    
    # Strategy 2: If still low confidence, use simple semantic search
    if intent_confidence < 0.5:
        print(f"[FALLBACK] Strategy 2: Simple semantic search (no filtering)")
        fallback_docs = vectorstore.similarity_search_with_score(query, k=50)
        return fallback_docs, "fallback_semantic_only"
    
    return doc_results, "no_fallback"


router = APIRouter()

qa_chain = setup_qa_chain(retriever)


# ============================================================================
# AUTHENTICATION MIDDLEWARE - Verify Microsoft Access Tokens
# ============================================================================

async def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify user is authenticated with a valid Microsoft access token.
    Can be disabled for testing by setting DISABLE_AUTH_FOR_TESTING=true in .env
    """
    # Check if auth is disabled for testing
    import os
    if os.getenv("DISABLE_AUTH_FOR_TESTING", "false").lower() == "true":
        print("[AUTH] Authentication DISABLED for testing")
        return {
            "user_id": "test_user",
            "name": "Test User",
            "email": "test@example.com"
        }
    
    # Normal authentication flow
    # This function:
    # 1. Checks if Authorization header is present
    # 2. Verifies the token with Microsoft Graph API
    # 3. Validates the user's email domain (@cloudfuze.com)
    # 4. Returns verified user information
    #
    # Raises:
    #     HTTPException: 401 if token is missing/invalid, 403 if domain not allowed
    #
    # Returns:
    #     dict: Verified user info (user_id, email, name)
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing or invalid authorization header. Please log in."
        )
    
    access_token = authorization.replace("Bearer ", "")
    
    try:
        # Verify token with Microsoft Graph API
        async with httpx.AsyncClient() as client:
            graph_response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0
            )
            
            if graph_response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid or expired access token. Please log in again."
                )
            
            user_info = graph_response.json()
            user_email = user_info.get("mail") or user_info.get("userPrincipalName", "")
            
            # Validate CloudFuze email domain
            if not user_email.endswith("@cloudfuze.com"):
                print(f"[AUTH] Access denied for non-CloudFuze email: {user_email}")
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: Only CloudFuze company accounts are allowed to access this application."
                )
            
            verified_user = {
                "user_id": user_info.get("id"),
                "email": user_email,
                "name": user_info.get("displayName", "User")
            }
            
            print(f"[AUTH] User authenticated: {user_email}")
            return verified_user
            
    except httpx.HTTPError as e:
        print(f"[AUTH] Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Unable to verify access token. Please log in again."
        )
    except HTTPException:
        # Re-raise HTTPExceptions (401/403)
        raise
    except Exception as e:
        print(f"[AUTH] Unexpected error during authentication: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during authentication"
        )

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

def extract_query_intent(question: str) -> str:
    """Extract user intent from the query."""
    question_lower = question.lower()
    
    if question.endswith("?"):
        if any(word in question_lower for word in ["how", "what", "why", "when", "where"]):
            return "request_information"
        elif any(word in question_lower for word in ["can", "could", "should", "is it possible"]):
            return "request_capability"
    
    if any(word in question_lower for word in ["download", "get", "need", "want"]):
        return "request_resource"
    elif any(word in question_lower for word in ["compare", "difference", "vs", "versus", "better"]):
        return "compare"
    elif any(word in question_lower for word in ["fix", "solve", "troubleshoot", "error"]):
        return "troubleshoot"
    elif any(word in question_lower for word in ["show", "list", "tell me"]):
        return "request_information"
    
    return "general_query"

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
    
    # Check for very short queries (ONLY 1-2 words, no question marks)
    # This ensures queries like "emojis ?" go through RAG, not conversational
    words = question.split()
    has_question_mark = '?' in question
    has_question_word = any(word in question_lower for word in ['what', 'how', 'why', 'when', 'where', 'who', 'which'])
    
    # Only treat as conversational if: very short (1-2 words), no '?', no question words
    if len(words) <= 2 and len(question.strip()) < 6 and not has_question_mark and not has_question_word:
        return True
    
    # Check if it's a simple greeting or social interaction (still allow short social phrases)
    social_words = ['hi', 'hello', 'hey', 'thanks', 'bye', 'good', 'nice', 'great', 'cool', 'awesome']
    if any(word in question_lower for word in social_words) and len(words) <= 2 and not has_question_mark:
        return True
    
    return False

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

# ============================================================================
# OPTION E: PERPLEXITY-STYLE RETRIEVAL FUNCTION
# ============================================================================

def perplexity_style_retrieve(
    query: str,
    k_dense: int = None,
    k_bm25: int = None,
    k_final: int = None,
    use_expansion: bool = None,
):
    """
    Perplexity-style retrieval:
      1. Optional LLM-based query expansion
      2. Dense retrieval from Chroma
      3. Sparse retrieval from BM25
      4. Merge + normalize scores
      5. Cross-encoder reranking
    """
    # Use config defaults if not provided
    if k_dense is None:
        k_dense = DENSE_RETRIEVAL_K
    if k_bm25 is None:
        k_bm25 = BM25_RETRIEVAL_K
    if k_final is None:
        k_final = FINAL_RETRIEVAL_K
    if use_expansion is None:
        use_expansion = ENABLE_QUERY_EXPANSION
    
    if not vectorstore:
        return []

    queries = [query]
    if use_expansion:
        try:
            expansions = query_expander.expand(query, n=3)
            print(f"[QUERY EXPANSION] {len(expansions)} expansions: {expansions}")
            queries.extend(expansions)
        except Exception as e:
            print(f"[WARN] Query expansion failed: {e}")

    # ---- 1. Dense retrieval (embeddings) ----
    dense_candidates = []
    for q in queries:
        try:
            # similarity_search_with_score returns (doc, distance) with lower=better
            results = vectorstore.similarity_search_with_score(q, k=k_dense)
            for doc, dist in results:
                dense_candidates.append((doc, float(dist)))
        except Exception as e:
            print(f"[WARN] Dense retrieval failed for query '{q}': {e}")

    # Deduplicate dense docs by id+content (keep best distance)
    dense_map = {}
    for doc, dist in dense_candidates:
        key = (doc.page_content[:120], doc.metadata.get("source_type", ""), doc.metadata.get("page_url", ""))
        if key not in dense_map or dist < dense_map[key][1]:
            dense_map[key] = (doc, dist)
    dense_list = list(dense_map.values())

    if dense_list:
        dists = [d for _, d in dense_list]
        d_min, d_max = min(dists), max(dists)
        def norm_dense(dist):
            # convert distance (0.2–0.8) to similarity (0–1)
            if d_max == d_min:
                return 1.0
            # smaller distance = higher similarity
            return (d_max - dist) / (d_max - d_min)
    else:
        norm_dense = lambda _: 0.0

    # ---- 2. Sparse retrieval (BM25) ----
    bm25_results = []
    if bm25_retriever:
        for q in queries:
            with suppress(Exception):
                bm25_results.extend(bm25_retriever.search(q, k=k_bm25))

        bm25_map = {}
        for doc, score in bm25_results:
            key = (doc.page_content[:120], doc.metadata.get("source_type", ""), doc.metadata.get("page_url", ""))
            if key not in bm25_map or score > bm25_map[key][1]:
                bm25_map[key] = (doc, score)
        bm25_list = list(bm25_map.values())

        if bm25_list:
            s = [s for _, s in bm25_list]
            s_min, s_max = min(s), max(s)
            def norm_bm25(score):
                if s_max == s_min:
                    return 1.0
                return (score - s_min) / (s_max - s_min)
        else:
            norm_bm25 = lambda _: 0.0
    else:
        bm25_list = []
        norm_bm25 = lambda _: 0.0

    # ---- 3. Merge dense + BM25 ----
    combined = {}
    for doc, dist in dense_list:
        key = (doc.page_content[:120], doc.metadata.get("source_type", ""), doc.metadata.get("page_url", ""))
        combined.setdefault(key, {"doc": doc, "dense": [], "bm25": []})
        combined[key]["dense"].append(dist)

    for doc, score in bm25_list:
        key = (doc.page_content[:120], doc.metadata.get("source_type", ""), doc.metadata.get("page_url", ""))
        combined.setdefault(key, {"doc": doc, "dense": [], "bm25": []})
        combined[key]["bm25"].append(score)

    candidates = []
    q_lower = query.lower()  # For metadata matching
    
    for key, info in combined.items():
        doc = info["doc"]
        meta = doc.metadata or {}
        
        if info["dense"]:
            dense_sim = max(norm_dense(d) for d in info["dense"])
        else:
            dense_sim = 0.0
        if info["bm25"]:
            bm25_sim = max(norm_bm25(s) for s in info["bm25"])
        else:
            bm25_sim = 0.0

        # Base score: DENSE_WEIGHT * dense + BM25_WEIGHT * bm25 (0–1)
        base_score = DENSE_WEIGHT * dense_sim + BM25_WEIGHT * bm25_sim
        
        # ---- Metadata-based boosts (generic, not hardcoded intents) ----
        # These boosts help surface relevant SharePoint docs that match query signals
        source_type = (meta.get("source_type") or meta.get("source") or "").lower()
        tag = (meta.get("tag") or "").lower()
        title = (meta.get("title") or meta.get("post_title") or "").lower()
        filename = (meta.get("filename") or "").lower()
        content_lower = doc.page_content.lower()

        # ---- Metadata-based boosting: SharePoint prioritization ----
        # Small general boost for SharePoint docs (internal documentation)
        # This helps prioritize internal docs over blog content
        if "sharepoint" in source_type or tag.startswith("sharepoint/"):
            base_score += 0.05

        candidates.append((doc, base_score))

    # Sort by base score descending
    candidates.sort(key=lambda x: x[1], reverse=True)

    # ---- 4. Cross-encoder reranking ----
    candidates = candidates[: max(k_final * 3, k_final)]  # pre-filter
    reranked = cross_reranker.rerank(query, candidates, top_k=k_final)

    return reranked  # list of (doc, final_score)


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
        
        # CloudFuze-focused conversational prompt
        conversational_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a CloudFuze AI assistant specializing in cloud migration services. For greetings like 'hi', 'hello', 'thanks', 'bye', respond warmly and professionally. For ANY other topics unrelated to CloudFuze, cloud migration, or enterprise services, politely redirect by saying: 'I don't have information about that topic, but I can help you with CloudFuze's migration services or products. What would you like to know?'"),
            ("human", "{question}")
        ])
        
        # Don't use conversation context - treat each question independently
        # conversation_context = await get_conversation_context(conversation_id)
        # enhanced_query = f"{conversation_context}\n\nUser: {question}" if conversation_context else question
        enhanced_query = question  # Use current question only
        
        chain = conversational_prompt | llm
        result = chain.invoke({"question": enhanced_query})
        answer = result.content
    else:
        # Handle informational queries with document retrieval
        # Don't use conversation context - treat each question independently
        # conversation_context = await get_conversation_context(conversation_id)
        enhanced_query = question  # Use current question only
        
        # ============ INTENT CLASSIFICATION ============
        # Classify user intent to enable branch-specific retrieval
        intent_result = classify_intent(question)
        intent = intent_result["intent"]
        intent_confidence = intent_result["confidence"]
        intent_method = intent_result.get("method", "unknown")
        
        print(f"[INTENT] Classified as '{intent}' (confidence: {intent_confidence:.2f}, method: {intent_method})")
        
        # Check if vectorstore is available
        if vectorstore is None:
            print("Warning: Vectorstore not initialized. Using default qa_chain.")
            result = qa_chain.invoke({"query": enhanced_query})
            answer = result["result"]
        else:
            try:
                # ============ QUERY EXPANSION ============
                # Expand query with intent-specific terms for better retrieval
                expanded_query = expand_query_with_intent(enhanced_query, intent)
                
                # ============ BRANCH-SPECIFIC RETRIEVAL ============
                # Use intent-based filtering to retrieve relevant documents
                RETRIEVAL_K = 50  # Number of documents to retrieve from vectorstore
                doc_results = retrieve_with_branch_filter(
                    query=expanded_query,
                    intent=intent,
                    k=RETRIEVAL_K
                )
                
                print(f"[RETRIEVAL] Retrieved {len(doc_results)} documents from '{intent}' branch")
                
                # ============ DETAILED VECTORDB LOGGING ============
                print(f"[VECTORDB] Detailed retrieval info:")
                for i, (doc, score) in enumerate(doc_results[:10]):  # Log top 10
                    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                    tag = metadata.get('tag', 'N/A')
                    source_type = metadata.get('source_type', 'N/A')
                    title = metadata.get('post_title', metadata.get('title', 'N/A'))
                    content_preview = doc.page_content[:100] if hasattr(doc, 'page_content') else 'N/A'
                    print(f"  [{i+1}] Score: {score:.4f} | Tag: {tag} | Source: {source_type} | Title: {title[:60]}")
                    print(f"      Content preview: {content_preview}...")
                
                # ============ CONFIDENCE-BASED FALLBACK ============
                # If confidence is low, try alternative retrieval strategies
                doc_results, fallback_strategy = confidence_based_fallback(
                    doc_results=doc_results,
                    intent=intent,
                    intent_confidence=intent_confidence,
                    query=enhanced_query
                )
                
                if fallback_strategy != "no_fallback":
                    print(f"[FALLBACK] Applied strategy: {fallback_strategy}, now have {len(doc_results)} docs")
                
                # ============ SOURCE PRIORITIZATION ============
                # Boost SharePoint documents to prioritize internal documentation
                PRIORITIZE_SHAREPOINT = True  # Set to False to disable prioritization
                SHAREPOINT_BOOST = 0.6  # Lower score = higher priority (0.6 = 40% boost)
                EMAIL_BOOST = 0.8  # 20% boost for emails
                
                if PRIORITIZE_SHAREPOINT:
                    boosted_docs = []
                    sharepoint_count = 0
                    email_count = 0
                    blog_count = 0
                    
                    for doc, score in doc_results:
                        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                        tag = metadata.get('tag', '').lower()
                        source_type = metadata.get('source_type', '').lower()
                        
                        # Apply source-based boosting
                        adjusted_score = score
                        if 'sharepoint' in tag or source_type == 'sharepoint':
                            adjusted_score = score * SHAREPOINT_BOOST
                            sharepoint_count += 1
                        elif 'email' in tag or source_type == 'email' or 'outlook' in tag:
                            adjusted_score = score * EMAIL_BOOST
                            email_count += 1
                        else:
                            blog_count += 1
                        
                        boosted_docs.append((doc, adjusted_score))
                    
                    # Re-sort by adjusted scores (lower is better)
                    boosted_docs.sort(key=lambda x: x[1])
                    doc_results = boosted_docs
                    
                    print(f"[PRIORITIZATION] Boosted sources - SharePoint: {sharepoint_count}, Email: {email_count}, Blog: {blog_count}")
                
                # ============ HYBRID RANKING ============
                # Combine semantic similarity with keyword matching
                doc_results = hybrid_ranking(
                    doc_results=doc_results,
                    query=question,  # Use original query for keyword matching
                    intent=intent,
                    alpha=0.7  # 70% semantic, 30% keyword
                )
                
                print(f"[HYBRID RANKING] Reranked {len(doc_results)} documents with semantic + keyword scores")
                
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
                
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", SYSTEM_PROMPT),
                    ("human", "Context: {context}\n\nQuestion: {question}")
                ])
                
                llm = ChatOpenAI(
                    model_name="gpt-4o-mini",
                    temperature=0.1,  # Low temperature for consistent responses
                    max_tokens=1500
                )
                
                chain = prompt_template | llm
                result = chain.invoke({
                    "context": context,
                    "question": enhanced_query
                })
                
                answer = result.content
                
            except Exception as e:
                print(f"[ERROR] Intent-based retrieval failed: {e}")
                # Fallback to original qa_chain if something goes wrong
                result = qa_chain.invoke({"query": enhanced_query})
                answer = result["result"]

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
            
            # Don't use conversation context - treat each question independently
            # conversation_context = await get_conversation_context(conversation_id)
            # enhanced_query = f"{conversation_context}\n\nUser: {question}" if conversation_context else question
            enhanced_query = question  # Use current question only
            conversation_context = None  # Set to None for metadata logging
            
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
                
                # CloudFuze-focused conversational prompt
                conversational_prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a CloudFuze AI assistant specializing in cloud migration services. For greetings like 'hi', 'hello', 'thanks', 'bye', respond warmly and professionally. For ANY other topics unrelated to CloudFuze, cloud migration, or enterprise services, politely redirect by saying: 'I don't have information about that topic, but I can help you with CloudFuze's migration services or products. What would you like to know?'"),
                    ("human", "{question}")
                ])
                
                # Stream the response
                full_response = ""
                messages = conversational_prompt.format_messages(question=enhanced_query)
                async for chunk in llm.astream(messages):
                    if hasattr(chunk, 'content'):
                        token = chunk.content
                        full_response += token
                        yield f"data: {json.dumps({'token': token, 'type': 'token'})}\n\n"
                        await asyncio.sleep(0.01)
                
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
            
            # ===== START RAG PIPELINE TRACING =====
            # Create structured Langfuse trace for RAG pipeline
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
                    }
                )
                
                # Start query processing span
                if rag_trace:
                    rag_trace.start_query(enhanced_query, metadata={"has_conversation_context": False})
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
                "query_intent": extract_query_intent(question),
                "is_conversational_query": is_conv,
                "query_length_words": len(question.split()),
                "query_length_chars": len(question),
                "has_followup": False,  # Conversation context disabled
            }
            
            try:
                # ====== PERPLEXITY-STYLE RAG (OPTION E) ======
                # Retrieve docs with dense + BM25 + reranker
                doc_results = perplexity_style_retrieve(
                    query=enhanced_query,
                    k_dense=40,
                    k_bm25=40,
                    k_final=8,
                    use_expansion=True,
                )

                final_docs = [doc for doc, score in doc_results]
                
                print(f"[RAG] Retrieved {len(final_docs)} docs using Option E pipeline")
                
                # You can still compute diversity metrics if you like
                diversity_metrics = calculate_document_diversity(
                    [(doc, 1.0) for doc in final_docs]
                )
                
                # For compatibility with existing code, create fallback variables
                intent = "option_e"
                intent_confidence = 1.0
                intent_method = "perplexity_style"
                fallback_strategy = "no_fallback"
                expanded_query = enhanced_query  # No expansion needed, handled by perplexity_style_retrieve
                    
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
                
                if not has_sharepoint and any(word in enhanced_query.lower() for word in ['sharepoint', 'document', 'file', 'folder', 'download', 'certificate']):
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
                import traceback
                traceback.print_exc()
                final_docs = []
                # Initialize intent variables if not already set
                if 'intent' not in locals():
                    intent = "other"
                    intent_confidence = 1.0
                    intent_method = "error_fallback"
                if 'fallback_strategy' not in locals():
                    fallback_strategy = "no_retrieval"
            
            # Filter out documents with None page_content
            final_docs = [doc for doc in final_docs if doc.page_content is not None and doc.page_content.strip()]
            print(f"[DEBUG] Final documents for context: {len(final_docs)} (after filtering None content)")
            
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
                    
                    # ============ CONTEXT COMPRESSION (OPTION E) ============
                    if ENABLE_CONTEXT_COMPRESSION and len(context_text) > 8000:
                        print(f"[CONTEXT] Context too long ({len(context_text)} chars), compressing...")
                        try:
                            context_text = context_compressor.compress(final_docs, max_chars=8000)
                            print(f"[CONTEXT] Compressed length: {len(context_text)} chars")
                        except Exception as e:
                            print(f"[WARN] Context compression failed: {e}")
                            # Keep original context if compression fails
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
            
            # Create streaming LLM with low temperature for consistent responses
            llm = ChatOpenAI(
                model_name="gpt-4o-mini", 
                streaming=True, 
                temperature=0.1,  # Low temperature for more consistent, deterministic responses
                max_tokens=1500
            )
            
            # Create the prompt template
            from langchain_core.prompts import ChatPromptTemplate
            from config import SYSTEM_PROMPT
            
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", "Context: {context}\n\nQuestion: {question}")
            ])
            
            # ===== START SYNTHESIS SPAN =====
            if rag_trace:
                try:
                    rag_trace.start_synthesis(
                        context=context_text,
                        metadata={
                            "context_length": len(context_text),
                            "document_count": len(final_docs),
                            "model": "gpt-4o-mini",
                            "temperature": 0.1
                        }
                    )
                except Exception as e:
                    print(f"[WARNING] Failed to start synthesis: {e}")
            
            # Stream the response with real-time streaming
            full_response = ""
            messages = prompt_template.format_messages(context=context_text, question=enhanced_query)
            async for chunk in llm.astream(messages):
                if hasattr(chunk, 'content'):
                    token = chunk.content
                    full_response += token
                    yield f"data: {json.dumps({'token': token, 'type': 'token'})}\n\n"
                    # Removed sleep for faster streaming
            
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
            overall_confidence = calculate_confidence(
                intent_confidence=intent_confidence,
                retrieval_docs=len(final_docs),
                avg_similarity=avg_similarity
            )
            
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
                
                # ===== INTENT CLASSIFICATION (NEW) =====
                "intent": {
                    "detected": intent,
                    "confidence": intent_confidence,
                    "method": intent_method,
                    "branch_description": INTENT_BRANCHES.get(intent, {}).get("description", "Option E: Perplexity-style RAG")
                },
                
                # ===== CONFIDENCE SCORING (NEW) =====
                "confidence": {
                    "overall": overall_confidence,
                    "breakdown": {
                        "intent": intent_confidence,
                        "retrieval": min(len(final_docs) / 30.0, 1.0),
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
                    "method": "advanced_rag_pipeline",
                    "branch": intent,
                    "techniques_applied": ["intent_classification", "query_expansion", "hybrid_ranking", "diversity_scoring"],
                    "fallback_strategy": fallback_strategy,
                    "query_expansion": {
                        "original": question,
                        "expanded": expanded_query if 'expanded_query' in locals() else question,
                        "expansion_terms": INTENT_BRANCHES.get(intent, {}).get("query_expansion", [])
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
                        "has_history": False,  # Conversation context disabled
                        "turns": 0,
                        "size_chars": 0
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

@router.post("/chat/history/rebuild")
async def rebuild_chat_history(
    request: Request,
    current_user: dict = Depends(verify_user_access)
):
    """Rebuild chat history for a user after message editing. Protected against IDOR."""
    try:
        body = await request.json()
        user_id = body.get("user_id")
        messages = body.get("messages", [])
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Clear existing history first
        await clear_user_chat_history(user_id)
        
        # Re-add all messages in order
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            
            if role and content:
                await add_to_conversation(user_id, role, content)
        
        return {"message": f"Chat history rebuilt for user {user_id}", "message_count": len(messages)}
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
        result = chain.invoke({"prompt": prompt})
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
        improved_response = llm.invoke(correction_prompt).content
        
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
