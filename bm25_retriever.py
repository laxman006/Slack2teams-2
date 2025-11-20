# bm25_retriever.py
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
import re

class BM25Retriever:
    """
    Enhanced BM25 retriever that indexes both content AND metadata.
    
    This allows BM25 to match against:
    - Document content (page_content)
    - Title, filename, folder paths
    - Tags and source types
    
    This dramatically improves recall for queries that match metadata
    (e.g., "JSON Slack to Teams" matching filename "Slack to Teams Json Export.docx")
    """

    def __init__(self, documents: List[Document]):
        self.documents = documents
        # Build enriched text including metadata for each document
        self.tokenized_docs = [self._build_and_tokenize(d) for d in documents]
        self.bm25 = BM25Okapi(self.tokenized_docs)

    def _build_and_tokenize(self, doc: Document) -> List[str]:
        """
        Build searchable text from document content + metadata.
        
        This allows BM25 to match against filenames, folder paths, titles, etc.
        """
        meta = doc.metadata or {}

        # Extract useful metadata fields
        tag = meta.get("tag", "")
        title = meta.get("title", "") or meta.get("post_title", "")
        filename = meta.get("filename", "")
        folder_path = meta.get("folder_path", "")
        source_type = meta.get("source_type", "") or meta.get("source", "")
        
        # Combine all text for BM25 indexing
        # Weight: content is most important, but metadata provides strong signals
        full_text = " ".join([
            doc.page_content or "",
            str(tag),
            str(title),
            str(filename),
            str(folder_path),
            str(source_type),
        ])

        return self._tokenize(full_text)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase words (min 3 chars)."""
        text = text.lower()
        return [w for w in re.findall(r"\w+", text) if len(w) > 2]

    def search(self, query: str, k: int = 30) -> List[Tuple[Document, float]]:
        """Search documents using BM25 scoring."""
        tokens = self._tokenize(query)
        scores = self.bm25.get_scores(tokens)

        # Sort by score (higher = better)
        indexed = list(enumerate(scores))
        indexed.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in indexed[:k]:
            results.append((self.documents[idx], float(score)))
        return results

