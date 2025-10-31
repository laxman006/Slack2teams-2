# SharePoint Document Extraction - Quick Start

## ✅ Implementation Complete!

All components have been successfully implemented for extracting SharePoint documents and adding them to your MongoDB Atlas vector store with full citation support.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install New Dependencies

```bash
pip install python-pptx==0.6.23 aiohttp>=3.9.0
```

### Step 2: Run Extraction

```bash
python extract_sharepoint_documents.py
```

This will:
- ✅ Crawl SharePoint DOC360 site
- ✅ Download PDF, Word, Excel, PowerPoint, and text files
- ✅ Skip images and videos
- ✅ Process and chunk documents
- ✅ Generate embeddings
- ✅ Store in MongoDB Atlas

### Step 3: Test & Verify

```bash
python test_sharepoint_documents.py
```

This validates everything is working correctly.

---

## 📊 What Was Built

### New Files Created

1. **`app/sharepoint_document_crawler.py`**
   - Crawls SharePoint using Microsoft Graph API
   - Lists all document libraries and folders
   - Downloads files with metadata tracking
   - Handles pagination and rate limiting

2. **`app/powerpoint_processor.py`**
   - Extracts text from PowerPoint presentations
   - Processes slides, notes, and tables
   - Supports .pptx and .ppt formats

3. **`app/sharepoint_file_processor.py`**
   - Routes files to appropriate processors
   - Unified processing pipeline
   - Creates standardized metadata

4. **`extract_sharepoint_documents.py`**
   - Main orchestration script
   - Smart duplicate detection
   - Progress tracking and logging
   - Error handling and recovery

5. **`test_sharepoint_documents.py`**
   - Complete test suite
   - Validates extraction and citations
   - Tests LLM responses

6. **`SHAREPOINT_EXTRACTION_GUIDE.md`**
   - Complete usage documentation
   - Troubleshooting guide
   - Monitoring instructions

### Modified Files

1. **`config.py`**
   - Added citation instructions to SYSTEM_PROMPT
   - LLM now cites sources in responses

2. **`app/llm.py`**
   - Enhanced context formatting
   - Includes file metadata in context
   - Shows source, folder path, and dates

3. **`requirements.txt`**
   - Added python-pptx for PowerPoint support
   - Added aiohttp for async downloads

---

## 🎯 Key Features

### 1. **Comprehensive File Support**
- ✅ PDF documents
- ✅ Word documents (.docx, .doc)
- ✅ Excel spreadsheets (.xlsx, .xls)
- ✅ PowerPoint presentations (.pptx, .ppt)
- ✅ Text files (.txt, .md)
- ❌ Excludes: images, videos, archives

### 2. **Smart Duplicate Prevention**
- Tracks processed files
- Only processes new/updated documents
- Removes old versions when files are updated
- Saves time and API costs

### 3. **Rich Citation Metadata**

Each document chunk includes:
```python
{
  "file_name": "Migration_Guide.pdf",
  "file_type": "pdf",
  "sharepoint_url": "https://...",
  "folder_path": "/Shared Documents/Guides",
  "last_modified": "2025-10-15T10:30:00Z",
  "file_size_kb": 245,
  "chunk_index": 0
}
```

### 4. **Automatic Citations in Responses**

LLM responses now include sources:
```
CloudFuze supports multi-user migrations and maintains data integrity 
[Source: Migration_Guide.pdf - /Shared Documents/Guides]

The setup process involves three main steps 
[Source: Setup_Instructions.docx, Modified: 2025-10-10]
```

### 5. **Zero-Downtime Updates**
- Documents stored in MongoDB Atlas (cloud)
- Changes are immediately available
- **No redeployment needed!**
- Your deployed app queries MongoDB in real-time

---

## 💡 How It Works

### The Pipeline

```
SharePoint DOC360
    ↓
[1] Crawl & List Files (Graph API)
    ↓
[2] Download Files (filter by type)
    ↓
[3] Process & Extract Text
    ├── PDF Processor
    ├── Word Processor
    ├── Excel Processor
    ├── PowerPoint Processor
    └── Text Processor
    ↓
[4] Chunk Documents (1500 chars, 300 overlap)
    ↓
[5] Generate Embeddings (OpenAI ada-002)
    ↓
[6] Store in MongoDB Atlas
    ↓
✅ Available to LLM Immediately!
```

### Vector Storage & Retrieval

```
User Question
    ↓
Generate Query Embedding
    ↓
Search MongoDB Vector Store (cosine similarity)
    ↓
Retrieve Top K Documents (with metadata)
    ↓
Format Context (with citations)
    ↓
LLM Response (with sources)
```

---

## 📈 Expected Results

### After Running Extraction:

```
======================================================================
EXTRACTION COMPLETE - SUMMARY
======================================================================
Files crawled: 45
Files downloaded: 12
Files processed: 12
Files skipped (already current): 33
Files updated: 0
Chunks created: 234
Chunks stored in MongoDB: 234
Duration: 127.45 seconds
======================================================================

✅ SUCCESS! SharePoint documents added to MongoDB vector store
   Your RAG model now has access to this knowledge base!
   No deployment needed - changes are live immediately.
```

### Test Results:

```
======================================================================
TEST SUMMARY
======================================================================
✅ PASS - MongoDB Connection
✅ PASS - SharePoint Documents Exist
✅ PASS - Document Retrieval
✅ PASS - Citation Format
✅ PASS - File Types Coverage
✅ PASS - LLM Response with Citations
----------------------------------------------------------------------
Passed: 6/6

🎉 All tests passed!
```

---

## 🔄 Regular Updates

To keep your knowledge base current:

### Option 1: Manual Updates
```bash
# Run whenever SharePoint content changes
python extract_sharepoint_documents.py
```

### Option 2: Scheduled Updates (Recommended)

**Linux/Mac (crontab):**
```bash
# Every Sunday at 2 AM
0 2 * * 0 cd /path/to/project && /path/to/venv/bin/python extract_sharepoint_documents.py
```

**Windows (Task Scheduler):**
- Create task that runs weekly
- Action: `python.exe extract_sharepoint_documents.py`
- Start in: Your project directory

---

## 📋 Environment Variables Checklist

Ensure these are set in your `.env` file:

- [x] `OPENAI_API_KEY` - OpenAI API key
- [x] `MICROSOFT_CLIENT_ID` - Azure AD App ID
- [x] `MICROSOFT_CLIENT_SECRET` - Azure AD App Secret
- [x] `SHAREPOINT_SITE_URL` - Your SharePoint site URL
- [x] `MONGODB_URL` - MongoDB Atlas connection string
- [x] `MONGODB_VECTORSTORE_COLLECTION` - Collection name
- [ ] `SHAREPOINT_MAX_FILE_SIZE_MB` - Optional (default: 50)

---

## 🆘 Troubleshooting

### Common Issues

**1. "No files found"**
- Check SharePoint authentication
- Verify service principal permissions
- Confirm SHAREPOINT_SITE_URL is correct

**2. "OpenAI API error"**
- Check OPENAI_API_KEY is valid
- Ensure sufficient API credits
- Watch for rate limits

**3. "MongoDB connection failed"**
- Verify MONGODB_URL format
- Check IP whitelist in Atlas
- Ensure user has write permissions

**4. "Module not found: pptx"**
```bash
pip install python-pptx
```

See `SHAREPOINT_EXTRACTION_GUIDE.md` for complete troubleshooting.

---

## 📚 Documentation

For more details, see:
- **`SHAREPOINT_EXTRACTION_GUIDE.md`** - Complete usage guide
- **`sharepoint-document-vectorization.plan.md`** - Implementation plan
- **`MONGODB-VECTORSTORE-SUMMARY.md`** - Vector store details

---

## 🎉 Success Criteria

You'll know it's working when:

1. ✅ Extraction script runs without errors
2. ✅ MongoDB shows new documents in collection
3. ✅ Test suite passes all 6 tests
4. ✅ Chatbot responds with citations
5. ✅ Citations include file names and folder paths

---

## 🚦 Next Steps

1. **Install dependencies:**
   ```bash
   pip install python-pptx aiohttp
   ```

2. **Run extraction:**
   ```bash
   python extract_sharepoint_documents.py
   ```

3. **Verify:**
   ```bash
   python test_sharepoint_documents.py
   ```

4. **Test your chatbot** - Ask questions and see citations!

5. **Schedule updates** - Keep knowledge base current

6. **Monitor MongoDB Atlas** - Track usage and performance

---

## 💪 What You Can Do Now

- ✅ Extract all SharePoint documents automatically
- ✅ Get comprehensive citations in responses
- ✅ Update knowledge base without redeployment
- ✅ Support PDF, Word, Excel, PowerPoint files
- ✅ Track document sources and modifications
- ✅ Scale to large document collections
- ✅ Schedule automated updates
- ✅ Build user trust with transparent sources

---

**🎊 Congratulations! Your RAG system is now powered by a comprehensive, cited knowledge base from SharePoint!**

Ready to run? Start with:
```bash
pip install python-pptx aiohttp
python extract_sharepoint_documents.py
```

