# reranker.py
from typing import List, Tuple, Optional
from langchain_core.documents import Document

class CrossEncoderReranker:
    """
    Cross-encoder reranker using sentence-transformers.
    Install: pip install sentence-transformers
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
            print(f"[OK] CrossEncoder model loaded: {model_name}")
        except Exception as e:
            print(f"[WARN] Could not load CrossEncoder model: {e}")
            self.model = None

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[Document, float]],
        top_k: int = 6,
    ) -> List[Tuple[Document, float]]:
        """
        candidates: list of (doc, base_score) where base_score is combined dense+bm25.
        Returns: list of (doc, final_score) sorted descending.
        """
        if not self.model or not candidates:
            return candidates[:top_k]

        pairs = [[query, d.page_content] for d, _ in candidates]
        scores = self.model.predict(pairs)  # higher is better

        reranked = []
        for (doc, base_score), ce_score in zip(candidates, scores):
            # Combine: 80% cross-encoder, 20% base score
            final_score = 0.8 * float(ce_score) + 0.2 * float(base_score)
            reranked.append((doc, final_score))

        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked[:top_k]

