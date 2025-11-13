# -*- coding: utf-8 -*-
"""
Langfuse Prompt Management
Fetches prompts from Langfuse with fallback to config.py
"""

from langfuse import Langfuse
from config import SYSTEM_PROMPT, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# FEATURE FLAG: Disable Langfuse prompt fetching (use config.py only)
# Set to False to always use config.py SYSTEM_PROMPT
# Langfuse observability (tracing/logging) remains active
# ============================================================================
ENABLE_LANGFUSE_PROMPTS = False  # Set to True to fetch prompts from Langfuse

# Initialize Langfuse client for prompt management
try:
    langfuse_prompt_client = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST
    )
    print("[OK] Langfuse prompt manager initialized")
    if not ENABLE_LANGFUSE_PROMPTS:
        print("[INFO] Langfuse prompt fetching DISABLED - using config.py SYSTEM_PROMPT only")
        print("[INFO] Langfuse observability (tracing/logging) remains ACTIVE")
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
    # Check feature flag first - if disabled, use config.py immediately
    if not ENABLE_LANGFUSE_PROMPTS:
        print(f"✅ [PROMPT] Using config.py SYSTEM_PROMPT (Langfuse prompts disabled)")
        return None, {
            "source": "config.py",
            "prompt_name": "local_system_prompt",
            "version": "config.py"
        }
    
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


def _escape_curly_braces(text: str) -> str:
    """
    Escape curly braces in text for LangChain template compatibility.
    LangChain's ChatPromptTemplate treats {variable} as template variables,
    so we need to escape literal braces as {{ and }}.
    """
    return text.replace("{", "{{").replace("}", "}}")


def compile_prompt(prompt_template, context: str, question: str):
    """
    Compile prompt with variables. Handles both Langfuse prompts and plain text.
    
    CRITICAL: This function returns a prompt with curly braces already escaped
    for LangChain's ChatPromptTemplate. Do NOT escape the output again.
    
    Args:
        prompt_template: Langfuse prompt object, plain text string, or None (for fallback)
        context: Retrieved context from RAG (will be escaped internally)
        question: User's question (will be escaped internally)
        
    Returns:
        Compiled prompt text with all curly braces properly escaped
    """
    # CRITICAL: Escape curly braces in context and question FIRST
    # This prevents issues with SharePoint docs containing {workspace}, {adminCloudId}, etc.
    safe_context = _escape_curly_braces(context)
    safe_question = _escape_curly_braces(question)
    
    # Case 1: Langfuse prompt object with .compile() method
    if prompt_template and hasattr(prompt_template, "compile"):
        try:
            # Get raw prompt text from Langfuse (avoid triggering their template engine)
            try:
                prompt_text = str(prompt_template.prompt)
            except:
                # If even accessing .prompt fails, try the config attribute
                prompt_text = str(prompt_template.config.get("prompt", ""))
            
            # Remove {{context}} and {{question}} placeholders completely
            # (These are Langfuse template variables that we're bypassing)
            prompt_text = prompt_text.replace("{{context}}", "").replace("{{question}}", "")
            
            # Escape any curly braces in the system prompt itself
            safe_prompt_text = _escape_curly_braces(prompt_text)
            
            # Manually append escaped context and question
            final_prompt = f"{safe_prompt_text}\n\nContext from knowledge base:\n{safe_context}\n\nUser's Question:\n{safe_question}"
            
            print(f"[PROMPT] Compiled Langfuse prompt with proper escaping")
            return final_prompt
        except Exception as e:
            logger.error(f"Failed to compile Langfuse prompt: {e}")
            print(f"⚠️ [PROMPT] Compilation failed, using fallback: {e}")
            # Fall through to fallback
    
    # Case 2: Plain text template string
    elif prompt_template and isinstance(prompt_template, str):
        try:
            # Escape the template itself first
            safe_template = _escape_curly_braces(prompt_template)
            # Append escaped context and question
            compiled = f"{safe_template}\n\nContext: {safe_context}\n\nQuestion: {safe_question}"
            print(f"[PROMPT] Compiled text template with proper escaping")
            return compiled
        except Exception as e:
            logger.error(f"Failed to compile text template: {e}")
            print(f"⚠️ [PROMPT] Text template failed, using fallback: {e}")
            # Fall through to fallback
    
    # Case 3: Fallback to config.py prompt
    safe_system_prompt = _escape_curly_braces(SYSTEM_PROMPT)
    fallback_prompt = f"{safe_system_prompt}\n\nContext: {safe_context}\n\nQuestion: {safe_question}"
    print(f"[PROMPT] Using config.py fallback prompt with proper escaping")
    return fallback_prompt

