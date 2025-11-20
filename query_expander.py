# query_expander.py
from typing import List
from langchain_openai import ChatOpenAI

class QueryExpander:
    """
    LLM-based query expansion for improving retrieval recall.
    
    Uses newline-separated format (more robust than JSON) to generate
    alternative phrasings and synonyms for the user's query.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model_name=model_name, 
            temperature=0.3,
            request_timeout=10  # 10 second timeout to avoid hanging
        )

    def expand(self, query: str, n: int = 3) -> List[str]:
        """
        Expand query into semantically related rewrites.
        
        Returns:
            List of alternative query strings (deduped, excluding original)
        """
        prompt = f"""You are helping a search system for technical documentation.

Given the user query below, generate {n} alternative ways of asking the same thing:
- Use different synonyms
- Use related technical terms
- Keep each variation short (max 15 words)

Return ONLY the variations, each on a new line, no numbering, no bullets, no extra text.

Query: "{query}"

Variations:"""
        
        try:
            resp = self.llm.invoke(prompt)
            if not resp or not resp.content:
                print(f"[WARN] Query expansion returned empty response")
                return []
            
            text = resp.content.strip()
            if not text:
                print(f"[WARN] Query expansion returned empty content")
                return []
            
            # Parse newline-separated variations
            lines = []
            for line in text.splitlines():
                # Clean up common prefixes (1., -, *, etc.)
                line = line.strip()
                line = line.lstrip("0123456789.-*• ").strip()
                if line:
                    lines.append(line)
            
            # Dedup + remove exact original
            uniq = []
            query_lower = query.lower()
            for q in lines:
                if q and q.lower() != query_lower and q not in uniq:
                    uniq.append(q)
            
            result = uniq[:n]
            if not result:
                print(f"[WARN] Query expansion produced no valid variations, continuing without expansion")
            
            return result
            
        except TimeoutError:
            print(f"[WARN] Query expansion timed out after 10s, continuing without expansion")
            return []
        except Exception as e:
            # Log the error type for better debugging
            print(f"[WARN] Query expansion failed ({type(e).__name__}): {e}")
            return []

