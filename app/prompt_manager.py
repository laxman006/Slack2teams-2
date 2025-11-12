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
    Compile prompt with variables. Handles both Langfuse prompts and plain text.
    
    Args:
        prompt_template: Langfuse prompt object, plain text string, or None (for fallback)
        context: Retrieved context from RAG
        question: User's question
        
    Returns:
        Compiled prompt text or messages (consistent format)
    """
    # Case 1: Langfuse prompt object with .compile() method
    if prompt_template and hasattr(prompt_template, "compile"):
        try:
            # CRITICAL FIX: Completely bypass Langfuse's template engine
            # Context may contain ANY curly braces ({workspace}, {adminCloudId}, etc.) that break parsing
            # Strategy: Strip out {{context}} and {{question}} placeholders, append them manually
            
            # Try to get raw prompt text (this might still trigger template parsing in some Langfuse versions)
            try:
                prompt_text = str(prompt_template.prompt)
            except:
                # If even accessing .prompt fails, try the config attribute
                prompt_text = str(prompt_template.config.get("prompt", ""))
            
            # Remove {{context}} and {{question}} placeholders completely
            prompt_text = prompt_text.replace("{{context}}", "").replace("{{question}}", "")
            
            # Manually append context and question at the end (no template substitution)
            final_prompt = f"{prompt_text}\n\nContext from knowledge base:\n{context}\n\nUser's Question:\n{question}"
            
            print(f"[PROMPT] Compiled Langfuse prompt successfully (bypassed template engine)")
            return final_prompt
        except Exception as e:
            logger.error(f"Failed to compile Langfuse prompt: {e}")
            print(f"⚠️ [PROMPT] Compilation failed, using fallback: {e}")
            # Fall through to fallback
    
    # Case 2: Plain text template string
    elif prompt_template and isinstance(prompt_template, str):
        try:
            # Try to format the string with context and question
            compiled = prompt_template.format(context=context, question=question)
            print(f"[PROMPT] Compiled text template successfully")
            return compiled
        except KeyError:
            # Template doesn't have the expected placeholders, use as-is with additions
            compiled = f"{prompt_template}\n\nContext: {context}\n\nQuestion: {question}"
            print(f"[PROMPT] Using text template with appended context")
            return compiled
        except Exception as e:
            logger.error(f"Failed to compile text template: {e}")
            print(f"⚠️ [PROMPT] Text template failed, using fallback: {e}")
            # Fall through to fallback
    
    # Case 3: Fallback to config.py prompt
    fallback_prompt = f"{SYSTEM_PROMPT}\n\nContext: {context}\n\nQuestion: {question}"
    print(f"[PROMPT] Using config.py fallback prompt")
    return fallback_prompt

