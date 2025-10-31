# SharePoint Document Extraction Guide

Complete guide for extracting SharePoint documents and adding them to your MongoDB Atlas vector store for RAG.

## 🎯 Overview

This system extracts documents from SharePoint DOC360, processes them, and adds them to your MongoDB Atlas vector store. Your deployed application will **immediately** have access to this knowledge base without any redeployment.

### Supported File Types

✅ **Included:**
- PDF files (`.pdf`)
- Word documents (`.docx`, `.doc`)
- Excel spreadsheets (`.xlsx`, `.xls`)
- PowerPoint presentations (`.pptx`, `.ppt`)
- Text files (`.txt`, `.md`)

❌ **Excluded:**
- Images (`.png`, `.jpg`, `.gif`, etc.)
- Videos (`.mp4`, `.avi`, `.mov`, etc.)
- Archives and executables

---

## 📋 Prerequisites

### 1. Environment Variables

Ensure these are set in your `.env` file:

```env
# Required - OpenAI
OPENAI_API_KEY=your_openai_api_key

# Required - Microsoft/SharePoint Authentication
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
MICROSOFT_TENANT=cloudfuze.com

# Required - SharePoint Site
SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360

# Required - MongoDB Atlas
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=slack2teams
MONGODB_VECTORSTORE_COLLECTION=cloudfuze_vectorstore

# Optional - File Size Limit (default: 50 MB)
SHAREPOINT_MAX_FILE_SIZE_MB=50
```

### 2. Install New Dependencies

```bash
pip install python-pptx==0.6.23 aiohttp>=3.9.0
```

Or simply update all dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

### Step 1: Extract SharePoint Documents

Run the extraction script:

```bash
python extract_sharepoint_documents.py
```

This will:
1. ✅ Crawl your SharePoint DOC360 site
2. ✅ List all document libraries and folders
3. ✅ Download supported files
4. ✅ Process and chunk documents
5. ✅ Generate embeddings with OpenAI
6. ✅ Store in MongoDB Atlas vector store

**Expected Output:**
```
======================================================================
SHAREPOINT DOCUMENT EXTRACTION
======================================================================
Target Site: https://cloudfuzecom.sharepoint.com/sites/DOC360
MongoDB Collection: cloudfuze_vectorstore
======================================================================

STEP 1: CRAWLING SHAREPOINT
...
[OK] Found 45 files to process

STEP 2: DOWNLOADING FILES
...
[OK] Downloaded 45/45 files

STEP 3: PROCESSING FILES
...
[OK] Created 234 document chunks

STEP 4: STORING IN MONGODB VECTOR STORE
...
[OK] Stored 234 chunks in MongoDB

✅ SUCCESS! SharePoint documents added to MongoDB vector store
```

### Step 2: Verify Extraction

Run the test suite:

```bash
python test_sharepoint_documents.py
```

This validates:
- ✅ MongoDB connection
- ✅ SharePoint documents exist
- ✅ Document retrieval works
- ✅ Citations are properly formatted
- ✅ LLM responses include sources
- ✅ All file types are represented

### Step 3: Test Your Chatbot

Your chatbot **immediately** has access to the new knowledge base! No deployment needed.

Test it by asking questions like:
- "What are the migration steps?"
- "How do I configure the system?"
- "What is the setup process?"

Responses should include citations like:
```
CloudFuze supports multi-user migrations with automatic scheduling 
[Source: Migration_Guide.pdf - /Shared Documents/Guides]

The setup process involves three main steps [Source: Setup_Instructions.docx]
```

---

## 🔄 Running Updates

### Adding New Documents

Simply run the extraction script again:

```bash
python extract_sharepoint_documents.py
```

The script includes **smart duplicate detection**:
- ✅ **New files**: Added to vector store
- ✅ **Updated files**: Old chunks removed, new ones added
- ✅ **Unchanged files**: Skipped (no unnecessary processing)

Changes are **immediately available** to your deployed application!

### Scheduled Updates

To keep your knowledge base current, schedule the extraction script to run:

**Linux/Mac (cron):**
```bash
# Run every Sunday at 2 AM
0 2 * * 0 /path/to/venv/bin/python /path/to/extract_sharepoint_documents.py
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., weekly)
4. Action: Run `python.exe extract_sharepoint_documents.py`

---

## 📊 Monitoring & Logs

### Extraction Logs

After each run, check:

**Summary:** `data/sharepoint_extraction_summary.json`
```json
{
  "files_crawled": 45,
  "files_downloaded": 12,
  "files_processed": 12,
  "files_skipped": 33,
  "chunks_created": 234,
  "chunks_stored": 234,
  "duration_seconds": 127.45
}
```

**Processing Log:** `data/sharepoint_extraction_log.json`
- Tracks which files have been processed
- Stores file hashes for duplicate detection
- Records last processing timestamp

### MongoDB Atlas Dashboard

Monitor your vector store in MongoDB Atlas:
1. Go to your cluster
2. Navigate to Collections
3. Find your `cloudfuze_vectorstore` collection
4. Check document count and storage size

---

## 🎯 How Citations Work

### 1. Metadata Storage

Each document chunk stores rich metadata:

```python
{
  "text": "actual content here...",
  "embedding": [0.023, -0.015, ...],
  "metadata": {
    "source_type": "sharepoint_document",
    "file_name": "Migration_Guide.pdf",
    "file_type": "pdf",
    "sharepoint_url": "https://...",
    "folder_path": "/Shared Documents/Guides",
    "last_modified": "2025-10-15T10:30:00Z",
    "chunk_index": 0
  }
}
```

### 2. Context Formatting

When documents are retrieved, they're formatted with source information:

```
[Document 1] (Source: Migration_Guide.pdf - /Shared Documents/Guides, Modified: 2025-10-15)
Content about migration process...

[Document 2] (Source: Setup_Instructions.docx, Modified: 2025-10-10)
Step-by-step setup guide...
```

### 3. LLM Citation Instructions

The system prompt instructs the LLM to:
- Cite sources after factual statements
- Include file names and folder paths
- Reference page numbers for PDFs when available
- Format citations consistently

---

## 🔧 Troubleshooting

### Issue: No files found

**Cause:** Authentication or permissions issue

**Solution:**
1. Verify `MICROSOFT_CLIENT_ID` and `MICROSOFT_CLIENT_SECRET`
2. Ensure the service principal has read access to SharePoint
3. Check `SHAREPOINT_SITE_URL` is correct

### Issue: Files downloaded but not processed

**Cause:** Missing processor dependencies

**Solution:**
```bash
pip install python-pptx python-docx openpyxl PyPDF2
```

### Issue: Embeddings fail

**Cause:** OpenAI API key issue

**Solution:**
1. Verify `OPENAI_API_KEY` is set
2. Check API key has sufficient credits
3. Ensure no rate limiting issues

### Issue: MongoDB connection fails

**Cause:** Connection string or network issue

**Solution:**
1. Verify `MONGODB_URL` format
2. Check IP whitelist in MongoDB Atlas
3. Ensure database user has write permissions

---

## 🎉 Benefits

### 1. **Zero-Downtime Updates**
- Add documents to MongoDB Atlas
- Changes are immediately available
- No application redeployment needed

### 2. **Smart Duplicate Prevention**
- Tracks processed files
- Only processes new/updated documents
- Saves time and API costs

### 3. **Rich Citations**
- Every response includes sources
- Users see exactly where information comes from
- Builds trust and transparency

### 4. **Scalable Architecture**
- MongoDB Atlas handles large datasets
- Cosine similarity search is efficient
- Can add vector search indexes for better performance

### 5. **Comprehensive File Support**
- PDF, Word, Excel, PowerPoint, Text
- Preserves document structure
- Handles tables, images (text extraction), and formatting

---

## 📚 Files Created

### New Files
- `app/sharepoint_document_crawler.py` - Crawls SharePoint via Graph API
- `app/powerpoint_processor.py` - Extracts text from presentations
- `app/sharepoint_file_processor.py` - Routes files to processors
- `extract_sharepoint_documents.py` - Main extraction script
- `test_sharepoint_documents.py` - Test suite
- `SHAREPOINT_EXTRACTION_GUIDE.md` - This guide

### Modified Files
- `config.py` - Added citation instructions to SYSTEM_PROMPT
- `app/llm.py` - Enhanced context formatting with metadata
- `requirements.txt` - Added python-pptx and aiohttp

---

## 💡 Next Steps

1. **Run the extraction:**
   ```bash
   python extract_sharepoint_documents.py
   ```

2. **Verify results:**
   ```bash
   python test_sharepoint_documents.py
   ```

3. **Test your chatbot** and see citations in action!

4. **Schedule regular updates** to keep knowledge base current

5. **Monitor MongoDB Atlas** for storage and performance

---

## 🆘 Support

If you encounter issues:

1. Check the logs in `data/sharepoint_extraction_summary.json`
2. Review error messages in console output
3. Verify all environment variables are set
4. Ensure all dependencies are installed
5. Check MongoDB Atlas connection and permissions

For more help, refer to the existing documentation:
- `MONGODB-VECTORSTORE-SUMMARY.md`
- `DEPLOYMENT-GUIDE.md`
- `START-HERE.md`

---

**🎉 Congratulations! Your RAG system now has access to comprehensive SharePoint documentation with full citations!**

