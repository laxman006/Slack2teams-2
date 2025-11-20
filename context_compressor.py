# context_compressor.py
from typing import List
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

class ContextCompressor:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model_name=model_name, temperature=0)

    def compress(self, docs: List[Document], max_chars: int = 8000) -> str:
        """
        Summarize multiple chunks into a compact context string.
        """
        full = "\n\n".join(d.page_content for d in docs)
        if len(full) <= max_chars:
            return full

        prompt = f"""
You are compressing context for a RAG chatbot.

Summarize the following documentation into a concise but complete set of notes.
Keep important details, steps, and distinctions.

Text:
\"\"\"
{full[:25000]}
\"\"\"
"""
        resp = self.llm.invoke(prompt)
        return resp.content

