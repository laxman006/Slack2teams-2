# -*- coding: utf-8 -*-
"""
Langfuse Prompt Management
Fetches prompts from Langfuse with fallback to config.py
"""

from langfuse import Langfuse
from config import SYSTEM_PROMPT, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
import logging

logger = logging.getLogger(__name__)

# Initialize Langfuse client for prompt management
try:
    langfuse_prompt_client = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST
    )
    print("[OK] Langfuse prompt manager initialized")
except Exception as e:
    print(f"[!] Langfuse prompt manager initialization failed: {e}")
    langfuse_prompt_client = None


def get_system_prompt(prompt_name: str = "cloudfuze-system-prompt", version: str = None):
    """
    Get system prompt from Langfuse with fallback to config.py.
    
    Args:
        prompt_name: Name of the prompt in Langfuse
        version: Specific version or None for latest
        
    Returns:
        Tuple of (prompt_template, prompt_metadata)
        prompt_template: Langfuse prompt object or None
        prompt_metadata: Dict with prompt info
    """
    if not langfuse_prompt_client:
        logger.warning("Langfuse prompt client not available, using fallback prompt")
        return None, {
            "source": "config.py",
            "prompt_name": "fallback",
            "version": "hardcoded"
        }
    
    try:
        # Fetch prompt from Langfuse
        if version:
            prompt = langfuse_prompt_client.get_prompt(prompt_name, version=version)
        else:
            prompt = langfuse_prompt_client.get_prompt(prompt_name)  # Latest version
        
        metadata = {
            "source": "langfuse",
            "prompt_name": prompt.name,
            "version": prompt.version,
            "config": prompt.config if hasattr(prompt, 'config') else {}
        }
        
        logger.info(f"✅ Loaded prompt from Langfuse: {prompt_name} v{prompt.version}")
        print(f"✅ [PROMPT] Loaded from Langfuse: {prompt_name} v{prompt.version}")
        return prompt, metadata
        
    except Exception as e:
        logger.error(f"❌ Failed to load prompt from Langfuse: {e}")
        print(f"⚠️ [PROMPT] Langfuse unavailable, using config.py fallback: {e}")
        return None, {
            "source": "config.py",
            "prompt_name": "fallback",
            "version": "hardcoded",
            "error": str(e)
        }


def compile_prompt(prompt_template, context: str, question: str):
    """
    Compile prompt with variables.
    
    Args:
        prompt_template: Langfuse prompt object or None (for fallback)
        context: Retrieved context from RAG
        question: User's question
        
    Returns:
        Compiled prompt text or messages
    """
    if prompt_template:
        # Use Langfuse prompt
        try:
            compiled = prompt_template.compile(
                context=context,
                question=question
            )
            print(f"[PROMPT] Compiled Langfuse prompt successfully")
            return compiled
        except Exception as e:
            logger.error(f"Failed to compile Langfuse prompt: {e}")
            print(f"⚠️ [PROMPT] Compilation failed, using fallback: {e}")
            # Fall through to fallback
    
    # Fallback: Use config.py prompt (existing behavior)
    fallback_prompt = f"{SYSTEM_PROMPT}\n\nContext: {context}\n\nQuestion: {question}"
    print(f"[PROMPT] Using config.py fallback prompt")
    return fallback_prompt

