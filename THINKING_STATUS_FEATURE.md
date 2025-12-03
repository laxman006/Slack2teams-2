# ChatGPT-Style Streaming Thinking Status Feature

## Overview
This feature provides real-time visibility into the backend RAG pipeline processing with **character-by-character streaming**, reducing user anxiety during response generation by showing exactly what the system is doing in a natural, conversational way.

## Backend Implementation

### Status Events Sent
The backend streams status updates during query processing:

1. **analyzing_query** - Initial query analysis
2. **expanding_query** - Query expansion (if enabled)
3. **retrieving_docs** - Searching the knowledge base
4. **reranking_docs** - Reranking documents for relevance (shows count)
5. **reading_sources** - Reading from specific sources (blog/SharePoint)
6. **selecting_docs** - Selecting top N documents
7. **generating** - Generating final response

### Implementation in `app/endpoints.py`
Status events are sent as SSE (Server-Sent Events):
```python
yield f"data: {json.dumps({'type': 'status', 'status': 'analyzing_query', 'message': 'Analyzing query'})}\n\n"
```

## Frontend Implementation

### UI Component (`frontend/src/app/globals.css`)
- **`.thinking`** - Reuses existing thinking animation style
- **`.thinking-dots`** - Three animated bouncing dots
- **Identical to existing UI** - No new styles needed

### JavaScript Handler (`frontend/src/app/page.tsx`)
The `streamStatusText()` function:
- Receives status updates from backend
- **Streams word-by-word** for natural appearance
- Shows **blinking cursor** during streaming
- **Replaces previous status** with new one (not cumulative)
- Auto-scrolls to keep status visible
- 30ms delay between words for smooth streaming

## Visual Appearance

**Word-by-Word Streaming (Using existing "Thinking..." style):**

```
Frame 1 (0.0s):
Analyzing • • •

Frame 2 (0.03s):
Analyzing query • • •

Frame 3 (0.3s):
Expanding • • •

Frame 4 (0.6s):
Expanding query • • •

Frame 5 (0.9s):
Expanding query for better results • • •

Frame 6 (1.2s):
Searching knowledge base • • •

Frame 7 (2.0s):
Found 48 documents, reranking • • •

Frame 8 (2.3s):
Found 48 documents, reranking for relevance • • •

... each status replaces the previous one, streaming word-by-word
(The • • • represents the animated bouncing dots)
```

**Key Features:**
- ✅ **Uses existing `.thinking` style** - matches your UI perfectly
- ✅ **Animated bouncing dots** - same 3-dot animation
- ✅ **Word-by-word streaming** for natural flow
- ✅ **Each status replaces previous** (not cumulative)
- ✅ **Italic gray text** (#666) for thinking appearance
- ✅ **Consistent with existing UI patterns**

## Configuration

### Enable/Disable Query Expansion
In `config.py`:
```python
ENABLE_QUERY_EXPANSION = True  # Shows "Expanding query" step
```

### Adjust Status Display Timing
In `app/endpoints.py`, adjust the sleep duration:
```python
await asyncio.sleep(0.1)  # Delay between status updates
```

## Benefits

1. **Reduced User Anxiety** - Users see progress instead of blank screen
2. **Transparency** - Users understand what the system is doing
3. **Trust Building** - Shows the sophisticated processing happening
4. **Debug Aid** - Helps identify bottlenecks in RAG pipeline
5. **Professional UX** - Matches modern AI chat interfaces (ChatGPT, Claude)

## Testing

1. Ask a complex question requiring document retrieval
2. Observe the status steps appearing in real-time
3. Status should progress: Query → Expansion → Retrieval → Reranking → Sources → Selection → Generation

## Future Enhancements

- Show estimated time remaining
- Add more granular steps (e.g., BM25 retrieval, dense retrieval separately)
- Display document titles being read
- Show retrieval scores/confidence

