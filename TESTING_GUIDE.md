# Enhanced Ingestion Testing Guide

This guide explains how to test the enhanced content ingestion pipeline with semantic chunking, deduplication, graph indexing, and unified metadata extraction.

## Prerequisites

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Key new dependencies:
- `unstructured[all-docs]` - For PPTX and complex PDF processing
- `pytesseract` - For OCR support
- `scikit-learn` - For deduplication
- `tiktoken` - For token counting

### 2. Configure Data Sources

Edit `.env` or set environment variables:

```bash
# Enable test sources
ENABLE_SHAREPOINT_SOURCE=true
ENABLE_OUTLOOK_SOURCE=true
ENABLE_WEB_SOURCE=true

# SharePoint configuration
SHAREPOINT_SITE_URL=https://your-site.sharepoint.com/sites/YourSite
SHAREPOINT_START_PAGE=  # Empty for Documents library

# Outlook configuration
OUTLOOK_USER_EMAIL=user@yourdomain.com
OUTLOOK_FOLDER_NAME=Inbox

# Blog configuration (limit for testing)
BLOG_MAX_PAGES=1
```

### 3. Set Up Authentication

Ensure you have valid credentials in `.env`:
- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET`
- `MICROSOFT_TENANT`
- `OPENAI_API_KEY`

## Running Tests

### Quick Test (Recommended First)

Test with a small dataset to verify everything works:

```bash
python test_enhanced_ingestion.py
```

This will:
1. ✅ Backup existing vectorstore
2. ✅ Collect sample data (limited to ~10 items per source)
3. ✅ Run enhanced ingestion pipeline
4. ✅ Generate ingestion report
5. ✅ Test retrieval with sample queries
6. ✅ Verify graph relationships

### Expected Output

```
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
  ENHANCED INGESTION TEST SUITE
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

================================================================================
  TEST 1: Backup Existing Vectorstore
================================================================================
[OK] Backup created successfully

================================================================================
  TEST 2: Data Collection
================================================================================
[*] Collecting SharePoint documents...
[OK] Collected 15 SharePoint documents

[*] Collecting Outlook emails...
[OK] Collected 10 Outlook documents

[*] Collecting blog posts...
[OK] Collected 10 blog documents

[OK] Total documents collected: 35

================================================================================
  TEST 3: Enhanced Ingestion Pipeline
================================================================================
[*] Processing 15 documents from sharepoint...
[*] Chunking with semantic strategy (target=800 tokens)...
[OK] Created 42 chunks
[*] Running deduplication (threshold=0.85)...
[OK] Deduplication: 2 duplicates found, 40 unique chunks
[*] Storing graph relationships...
[OK] Graph relationships stored

... (similar for other sources)

[*] Building vectorstore with 95 chunks...
[OK] Vectorstore created with HNSW graph indexing
[OK] Total chunks in vectorstore: 95

================================================================================
  INGESTION REPORT
================================================================================
...statistics...

================================================================================
  TEST 4: Retrieval Quality Testing
================================================================================
Query 1: "How to migrate from Slack to Microsoft Teams?"
----------------------------------------
Retrieved: 5 chunks
Sources: blog, sharepoint
File types: html, pdf

✅ ALL TESTS PASSED!
```

### Test Report Files

After running tests, you'll find:
- `test_ingest_report_[timestamp].txt` - Detailed ingestion statistics
- Backup in `./data/backups/chroma_db_backup_[timestamp]/`

## Configuration Options

All settings can be configured via environment variables or `config.py`:

### Chunking Configuration

```python
CHUNK_TARGET_TOKENS = 800      # Target chunk size in tokens
CHUNK_OVERLAP_TOKENS = 200     # Overlap between chunks
CHUNK_MIN_TOKENS = 150         # Minimum size (merge smaller)
```

### Deduplication

```python
ENABLE_DEDUPLICATION = True    # Enable dedup
DEDUP_THRESHOLD = 0.85         # Similarity threshold (85%)
```

### Unstructured Processing

```python
ENABLE_UNSTRUCTURED = True     # Use for complex files
ENABLE_OCR = True              # OCR for scanned PDFs
OCR_LANGUAGE = "eng"           # Language code
```

### Graph Storage

```python
ENABLE_GRAPH_STORAGE = True    # Store relationships
GRAPH_DB_PATH = "./data/graph_relations.db"
```

## Understanding Test Results

### 1. Ingestion Statistics

The report shows:
- **Total Documents**: Number of raw documents processed
- **Total Chunks**: Number of chunks created after semantic splitting
- **Duplicates Merged**: Number of duplicate chunks detected and merged
- **By Source**: Breakdown by source type (sharepoint, email, blog)
- **By File Type**: Distribution across file types (pdf, docx, pptx, xlsx, html, eml)

### 2. Chunking Statistics

- **Average Chunks per Document**: How many chunks each document produces
- **Average Chunk Size**: Average tokens and characters per chunk
- Should be close to `CHUNK_TARGET_TOKENS` (800)

### 3. Sample Chunks

The report includes 5 sample chunks showing:
- **Metadata**: source, filetype, filename, url, page_number, chunk_index, token_count
- **Content Preview**: First 200 characters of chunk text

### 4. Graph Relationships

Statistics on stored relationships:
- **Total Documents**: Documents in graph store
- **Total Chunks**: Chunks in graph store
- **Total Relationships**: All relationships created
- **Relationship Types**: DOCUMENT_CONTAINS_CHUNK, EMAIL_REPLIES_TO, etc.

### 5. Retrieval Quality

For each test query, check:
- **Number of results**: Should return requested number (default: 5)
- **Source diversity**: Results from multiple sources (not all from one file)
- **File type diversity**: Mix of file types when relevant
- **Relevance**: Top result should be contextually relevant

## Troubleshooting

### No Documents Collected

**Problem**: `[WARNING] No documents collected`

**Solutions**:
1. Check source enable flags in `config.py`
2. Verify authentication credentials in `.env`
3. Ensure SharePoint/Outlook URLs are correct
4. Check network connectivity
5. Verify permissions for SharePoint site and Outlook mailbox

### Ingestion Fails

**Problem**: `[ERROR] Ingestion failed`

**Solutions**:
1. Check OpenAI API key is valid
2. Ensure sufficient API quota
3. Verify file permissions for `./data/` directory
4. Check logs for specific error messages

### No Retrieval Results

**Problem**: Queries return 0 results

**Solutions**:
1. Verify vectorstore was created successfully
2. Check that chunks were added (look at ingestion report)
3. Try broader queries
4. Verify OpenAI embeddings are working

### Graph Store Issues

**Problem**: Graph relationships not created

**Solutions**:
1. Check `ENABLE_GRAPH_STORAGE=true`
2. Verify `./data/` directory is writable
3. Check for SQLite errors in logs

### Memory/Performance Issues

**Problem**: Out of memory or very slow processing

**Solutions**:
1. Start with smaller test dataset (limit to 5-10 files)
2. Reduce `CHUNK_TARGET_TOKENS` if processing very large documents
3. Disable `ENABLE_DEDUPLICATION` temporarily for faster processing
4. Process sources one at a time

## Advanced Testing

### Test Individual Components

#### Test Semantic Chunking

```python
from app.chunking_strategy import SemanticChunker
from langchain_core.documents import Document

chunker = SemanticChunker(target_tokens=800)
doc = Document(page_content="Your text here...", metadata={})
chunks = chunker.chunk_document(doc)

print(f"Created {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {chunk.metadata['token_count']} tokens")
```

#### Test Deduplication

```python
from app.deduplication import Deduplicator
from langchain_core.documents import Document

deduplicator = Deduplicator(threshold=0.85)
docs = [
    Document(page_content="This is a test", metadata={"source": "test1"}),
    Document(page_content="This is a test", metadata={"source": "test2"}),  # Duplicate
    Document(page_content="Different content", metadata={"source": "test3"})
]

unique_docs, stats = deduplicator.deduplicate_within_batch(docs)
print(f"Duplicates found: {stats['duplicates_found']}")
print(f"Unique docs: {len(unique_docs)}")
```

#### Test Graph Store

```python
from app.graph_store import get_graph_store

graph_store = get_graph_store()

# Add test data
graph_store.add_document(
    doc_id="test-doc-1",
    source="test",
    url="http://example.com",
    filename="test.pdf",
    filetype="pdf"
)

# Get statistics
stats = graph_store.get_stats()
print(stats)
```

## Full Dataset Testing

Once tests pass with sample data, run with full dataset:

1. Update configuration:
```python
BLOG_MAX_PAGES = 14  # All blog posts
# Keep all sources enabled
```

2. Run full ingestion:
```bash
python test_enhanced_ingestion.py
```

3. Monitor progress:
- Watch for memory usage
- Check ingestion report for statistics
- Verify no errors in logs

## Validation Queries

After full ingestion, test with domain-specific queries:

1. **Product features**: "What are CloudFuze's main features?"
2. **Migration topics**: "How to migrate from Box to Google Drive?"
3. **Pricing**: "What pricing plans are available?"
4. **Technical details**: "What file types are supported?"
5. **Email context**: "Show emails about [project name]"
6. **Documents**: "Find the [document name]"

## Success Criteria

Tests are successful when:

✅ All 5 tests pass (Backup, Collection, Ingestion, Retrieval, Graph)
✅ Ingestion report shows reasonable statistics
✅ All file types processed without errors (PDF, DOCX, PPTX, XLSX, HTML, emails)
✅ Chunks have correct size (~800 tokens)
✅ Deduplication finds and merges duplicates (if any)
✅ Graph relationships created for all documents
✅ Retrieval returns relevant, diverse results
✅ No errors in logs

## Next Steps After Successful Testing

1. ✅ Review ingestion report and sample chunks
2. ✅ Fine-tune chunking parameters if needed
3. ✅ Adjust deduplication threshold based on results
4. ✅ Run with full production dataset
5. ✅ Integrate with chatbot application
6. ✅ Monitor performance and quality
7. ✅ Set up automated testing/validation

## Support

For issues or questions:
1. Check error logs in console output
2. Review ingestion report for clues
3. Test individual components separately
4. Verify all dependencies installed correctly
5. Check environment variables are set

## Reference

- **Chunking**: See `app/chunking_strategy.py`
- **Deduplication**: See `app/deduplication.py`
- **Graph Store**: See `app/graph_store.py`
- **Configuration**: See `config.py`
- **Test Script**: See `test_enhanced_ingestion.py`

