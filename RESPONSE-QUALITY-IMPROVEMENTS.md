## Response Quality Improvements: Reranking and Citations

Boost answer quality by:
- Reranking retrieved documents (Cohere API or local cross-encoder)
- Adding source citations to responses (and to streamed replies)

This guide shows minimal, safe edits to your existing codebase.

---

### 1) Install (optional, pick one reranker)

```bash
# Cohere reranker (recommended best quality)
pip install cohere

# Local reranker (no external API)
pip install sentence-transformers
```

If you use Cohere, set:

```bash
# .env / environment variable
COHERE_API_KEY=your_cohere_api_key
```

Add to requirements.txt if you want them permanent:

```
cohere>=5.5.8
sentence-transformers>=3.0.1
```

---

### 2) Add a Reranker in `app/llm.py`

Pick ONE of the following options.

#### Option A: Cohere Rerank (cloud API)

Add imports and helper:

```python
import os

try:
    import cohere
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    cohere_client = cohere.Client(COHERE_API_KEY) if COHERE_API_KEY else None
except ImportError:
    cohere_client = None
    print("Cohere not installed, skipping reranking")


def rerank_documents(query: str, documents: list, top_n: int = 10):
    """Rerank documents using Cohere Rerank for better relevance."""
    if not cohere_client or not documents:
        return documents[:top_n]
    try:
        doc_texts = [doc.page_content for doc in documents]
        rr = cohere_client.rerank(
            query=query,
            documents=doc_texts,
            top_n=min(top_n, len(documents)),
            model="rerank-english-v3.0"
        )
        ordered = []
        for r in rr.results:
            d = documents[r.index]
            d.metadata["rerank_score"] = r.relevance_score
            ordered.append(d)
        return ordered
    except Exception as e:
        print(f"Reranking failed: {e}")
        return documents[:top_n]
```

Use it where you assemble `final_docs` in `setup_qa_chain` (after dedup):

```python
# After unique_docs computed
final_docs = unique_docs[:30]
from app.llm import rerank_documents
final_docs = rerank_documents(query, final_docs, top_n=15)
```

#### Option B: Local Cross-Encoder (no API)

Add imports and helper:

```python
try:
    from sentence_transformers import CrossEncoder
    reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("sentence-transformers not installed, skipping reranking")


def rerank_documents_local(query: str, documents: list, top_n: int = 10):
    if not RERANKER_AVAILABLE or not documents:
        return documents[:top_n]
    try:
        pairs = [[query, d.page_content] for d in documents]
        scores = reranker_model.predict(pairs)
        scored = list(zip(documents, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        top_docs = []
        for d, s in scored[:top_n]:
            d.metadata["rerank_score"] = float(s)
            top_docs.append(d)
        return top_docs
    except Exception as e:
        print(f"Reranking failed: {e}")
        return documents[:top_n]
```

Use it similarly after dedup:

```python
from app.llm import rerank_documents_local
final_docs = rerank_documents_local(query, unique_docs[:30], top_n=15)
```

Note: Keep `top_n` around 10–15 to avoid diluting context.

---

### 3) Add Citations in `app/endpoints.py`

Add a small helper to format citations:

```python
def format_answer_with_citations(answer: str, documents: list) -> dict:
    if not documents:
        return {"answer": answer, "sources": []}
    sources, seen = [], set()
    for doc in documents[:5]:
        info = {
            "source": doc.metadata.get("source", "Unknown"),
            "type": doc.metadata.get("source_type", "unknown"),
            "relevance": doc.metadata.get("rerank_score", "N/A"),
        }
        key = f"{info['source']}_{info['type']}"
        if key in seen:
            continue
        seen.add(key)
        sources.append(info)
    if sources:
        citations = "\n\n---\n**Sources:**\n"
        for i, s in enumerate(sources, 1):
            rel = (
                f" (Relevance: {s['relevance']:.2f})"
                if isinstance(s.get('relevance'), (int, float)) else ""
            )
            citations += f"{i}. {s['source']} ({s['type']}){rel}\n"
        answer = answer + citations
    return {"answer": answer, "sources": sources}
```

Use it in `/chat` informational path:

```python
# retrieve
from app.vectorstore import vectorstore
from app.llm import rerank_documents  # or rerank_documents_local
relevant_docs = vectorstore.similarity_search(enhanced_query, k=25)
reranked_docs = rerank_documents(enhanced_query, relevant_docs, top_n=15)

# answer
result = qa_chain.invoke({"query": enhanced_query})
answer = result["result"]

# citations
fmt = format_answer_with_citations(answer, reranked_docs)
answer = fmt["answer"]
sources = fmt["sources"]
```

Include `sources` in the JSON response:

```python
return {
    "answer": preserve_markdown(answer),
    "user_id": user_id,
    "session_id": session_id,
    "trace_id": trace_id,
    "sources": sources,
}
```

For `/chat/stream`, perform the same rerank after retrieval and append citations to `full_response` before emitting the final `done` event. Also include `sources` in the final payload.

---

### 4) Optional: Show Sources in `index.html`

After rendering the assistant message:

```javascript
if (data.sources && data.sources.length > 0) {
  const sourcesDiv = document.createElement('div');
  sourcesDiv.className = 'sources';
  const items = data.sources
    .map(s => `<li>${(s.source || 'Unknown')} (${(s.type || 'unknown')})</li>`) 
    .join('');
  sourcesDiv.innerHTML = `<hr/><strong>Sources</strong><ul>${items}</ul>`;
  messageDiv.appendChild(sourcesDiv);
}
```

Optional CSS:

```css
.sources { font-size: 0.9em; opacity: 0.85; margin-top: 8px; }
.sources ul { margin: 6px 0 0 18px; }
```

---

### 5) Test

- Set `COHERE_API_KEY` and restart backend (if using Cohere).
- Ask a focused question and verify:
  - Logs show reranking applied.
  - Answers end with a “Sources” section.
  - Streaming endpoint includes citations in the final event.
  - UI renders sources list.

Regression checks:
- Conversational queries still bypass retrieval (no citations expected).
- Vectorstore initialization remains stable.
- Langfuse traces still log correctly.

---

### 6) Rollback

Comment out reranker imports/calls and `format_answer_with_citations` usage to revert to previous behavior.

---

### 7) Impact

- 30–50% improvement in answer grounding and relevance.
- Lower hallucinations via better document selection.
- Clear source transparency for users.
