"""
Conversation Context Utilities
================================

Centralized utilities for handling conversation context and continuity.
This module provides consistent context injection across all endpoints.
"""

from typing import Tuple, Dict, Any, Optional


async def build_enhanced_query(
    user_id: str, 
    question: str,
    is_followup_function=None
) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """
    Build an enhanced query with conversation context.
    
    Args:
        user_id: User/conversation identifier
        question: User's current question
        is_followup_function: Function to check if question is a follow-up
    
    Returns:
        Tuple of (enhanced_query, clarification_message, relevance_dict)
        - enhanced_query: Question with context injected (None if needs clarification)
        - clarification_message: Message to send if clarification needed
        - relevance_dict: Dictionary with relevance metadata
    """
    from app.mongodb_memory import get_conversation_context
    
    try:
        # Get conversation context
        context = await get_conversation_context(user_id)
        
        # Check if this is a follow-up question
        relevance = {}
        if is_followup_function and context:
            relevance = await is_followup_function(question, context)
        else:
            # Default relevance structure
            relevance = {
                "is_related": False,
                "needs_clarification": False,
                "clarification_message": None,
                "current_topic": None,
                "intent": "general"
            }
        
        # Check if clarification is needed
        if relevance.get("needs_clarification", False):
            return None, relevance.get("clarification_message"), relevance
        
        # Build enhanced query with context if related
        if relevance.get("is_related", False) and context:
            enhanced_query = f"{context}\n\nCurrent question: {question}"
            print(f"[CONTEXT] Enhanced query with conversation history")
        else:
            enhanced_query = question
            print(f"[CONTEXT] Using original query (no history)")
        
        return enhanced_query, None, relevance
        
    except Exception as e:
        print(f"[CONTEXT] Error building enhanced query: {e}")
        # Return original question on error
        return question, None, {
            "is_related": False,
            "needs_clarification": False,
            "error": str(e)
        }


async def get_user_context(user_id: str) -> str:
    """
    Get conversation context for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        Conversation context string (empty if not available)
    """
    from app.mongodb_memory import get_conversation_context
    
    try:
        context = await get_conversation_context(user_id)
        return context or ""
    except Exception as e:
        print(f"[CONTEXT] Error fetching context: {e}")
        return ""


def format_conversation_history(messages: list, max_messages: int = 5) -> str:
    """
    Format conversation history into a readable string.
    
    Args:
        messages: List of message dictionaries
        max_messages: Maximum number of messages to include
    
    Returns:
        Formatted conversation history string
    """
    if not messages:
        return ""
    
    # Take last N messages
    recent_messages = messages[-max_messages:]
    
    formatted = []
    for msg in recent_messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        if role == "user":
            formatted.append(f"User: {content}")
        elif role == "assistant":
            formatted.append(f"Assistant: {content}")
    
    return "\n".join(formatted)


def should_use_context(question: str, context: str) -> bool:
    """
    Determine if conversation context should be used for this question.
    
    Args:
        question: User's question
        context: Conversation context
    
    Returns:
        True if context should be used
    """
    if not context or not question:
        return False
    
    # Keywords that indicate follow-up questions
    followup_indicators = [
        "what about",
        "how about",
        "can you",
        "tell me more",
        "explain",
        "clarify",
        "also",
        "additionally",
        "furthermore",
        "and what",
        "what else",
        "anything else"
    ]
    
    question_lower = question.lower()
    
    # Check for follow-up indicators
    for indicator in followup_indicators:
        if indicator in question_lower:
            return True
    
    # Check for pronouns that might reference previous context
    pronouns = ["it", "that", "this", "they", "them", "their", "these", "those"]
    words = question_lower.split()
    
    for pronoun in pronouns:
        if pronoun in words:
            return True
    
    return False

