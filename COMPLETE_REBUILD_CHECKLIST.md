# ✅ Complete Vectorstore Rebuild Checklist

## 🎯 Goal
Rebuild vectorstore from scratch with:
- ✅ **ALL blog posts** from CloudFuze.com
- ✅ **ALL SharePoint files** from DOC360 site
- ✅ **ALL email threads** from last 6 months (presales@cloudfuze.com/Sent Items)
- ✅ **Enhanced features**: Semantic chunking, deduplication, graph relationships

---

## 📋 Pre-Rebuild Checklist

### ☑️ Step 1: Backup Current Vectorstore
```bash
python scripts/backup_vectorstore.py
```
**Result:** Creates backup in `./data/backups/chroma_db_backup_[timestamp]`

### ☑️ Step 2: Verify .env Configuration

**Required Settings:**
```bash
# ============================================================================
# VECTORSTORE INITIALIZATION
# ============================================================================
INITIALIZE_VECTORSTORE=true

# ============================================================================
# SOURCE CONFIGURATION - Enable ALL Sources
# ============================================================================
ENABLE_WEB_SOURCE=true
ENABLE_SHAREPOINT_SOURCE=true
ENABLE_OUTLOOK_SOURCE=true

# Disable local file sources (not needed)
ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false

# ============================================================================
# BLOG/WEB CONFIGURATION - ALL Blog Posts
# ============================================================================
WEB_URL=https://cloudfuze.com/wp-json/wp/v2/posts?per_page=100
WEB_START_PAGE=1
WEB_MAX_PAGES=100

# ============================================================================
# SHAREPOINT CONFIGURATION - ALL Files
# ============================================================================
SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360
SHAREPOINT_EXCLUDE_FILES=true

# ============================================================================
# OUTLOOK CONFIGURATION - ALL Threads (Last 6 Months)
# ============================================================================
OUTLOOK_USER_EMAIL=presales@cloudfuze.com
OUTLOOK_FOLDER_NAME=Sent Items
OUTLOOK_MAX_EMAILS=10000
OUTLOOK_DATE_FILTER=last_6_months

# ============================================================================
# ENHANCED INGESTION FEATURES (From enhanced-ing.plan.md)
# ============================================================================

# Chunking Configuration
CHUNK_TARGET_TOKENS=800
CHUNK_OVERLAP_TOKENS=200
CHUNK_MIN_TOKENS=150

# Deduplication
ENABLE_DEDUPLICATION=true
DEDUP_THRESHOLD=0.85

# Unstructured Library (for complex files: PPTX, scanned PDFs)
ENABLE_UNSTRUCTURED=true
ENABLE_OCR=true
OCR_LANGUAGE=eng

# Graph Storage (relationships in SQLite)
GRAPH_DB_PATH=./data/graph_relations.db
ENABLE_GRAPH_STORAGE=true

# ============================================================================
# OPENAI API KEY (REQUIRED)
# ============================================================================
OPENAI_API_KEY=your_actual_key_here

# ============================================================================
# MICROSOFT CREDENTIALS (REQUIRED)
# ============================================================================
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
MICROSOFT_TENANT=your_tenant_id
```

### ☑️ Step 3: Verify Dependencies Installed

Check that all required packages are installed:
```bash
pip list | findstr /i "unstructured pytesseract spacy scikit-learn chromadb"
```

**Expected to see:**
- unstructured
- pytesseract
- spacy
- scikit-learn
- chromadb

**If missing, install:**
```bash
pip install -r requirements.txt
```

---

## 🚀 Rebuild Process

### Step 1: Clear Current Vectorstore (Optional but Recommended)

**Option A: Delete and rebuild fresh**
```bash
# Backup first (if not done)
python scripts/backup_vectorstore.py

# Delete current vectorstore
Remove-Item -Recurse -Force ./data/chroma_db
```

**Option B: Let system rebuild automatically**
```bash
# System will detect INITIALIZE_VECTORSTORE=true and rebuild
# No manual deletion needed
```

### Step 2: Start Server for Full Ingestion
```bash
python server.py
```

### Step 3: Monitor Progress

Watch for these log sections:

#### 3a. Initialization Started
```
============================================================
>> INITIALIZING CF-CHATBOT KNOWLEDGE BASE
============================================================
[*] Checking for changed sources...
[*] Rebuilding vectorstore...
```

#### 3b. SharePoint Ingestion
```
============================================================
SHAREPOINT GRAPH API CONTENT EXTRACTION
============================================================
[OK] SharePoint access token obtained
[OK] Found site ID: ...
[OK] Connected to SharePoint via Graph API

[*] Depth 0: Extracting from: Documents
[*] Depth 1: Extracting from: Certificates
[*] Depth 2: Extracting from: Certificates > 2023
[*] Processing file: CloudFuze_SOC 2 Type 2 Report.pdf
[OK] Extracted file: ...
```

**What to look for:**
- ✅ Folders being scanned (Certificates, Documentation, Policy Documents, etc.)
- ✅ Files being extracted (PDF, DOCX, PPTX, XLSX)
- ✅ Success messages: `[OK] Extracted file: ...`
- ❌ Error messages: `[ERROR] Failed to extract...` (note these)

**Expected time:** 30-60 minutes for 1000+ files

#### 3c. Outlook Ingestion
```
[*] Processing Outlook emails...
[*] Outlook Processor initialized
   User: presales@cloudfuze.com
   Folder: Sent Items
   Date filter: last_6_months
[OK] Found folder ID for 'Sent Items'
[OK] Fetched X emails
[*] Grouping emails by conversation thread...
[OK] Created Y thread documents
```

**What to look for:**
- ✅ Folder found: `[OK] Found folder ID`
- ✅ Emails fetched: `[OK] Fetched X emails`
- ✅ Threads created: `[OK] Created Y thread documents`
- ❌ Folder not found: Check `OUTLOOK_FOLDER_NAME=Sent Items` (with space!)

**Expected time:** 20-40 minutes for 500-10,000 emails

#### 3d. Blog Ingestion
```
[*] Processing web content (blogs)...
[*] Fetching blog posts from: https://cloudfuze.com/wp-json/wp/v2/posts
[*] Page 1: Found X posts
[*] Page 2: Found X posts
...
[OK] Total blog posts fetched: Y
```

**What to look for:**
- ✅ Pages being fetched: `[*] Page X: Found Y posts`
- ✅ Total count: `[OK] Total blog posts fetched: Y`
- ✅ Should see multiple pages if you have 100+ posts

**Expected time:** 10-20 minutes for 100-500 posts

#### 3e. Enhanced Processing
```
[*] Applying semantic chunking...
[*] Chunking X documents...
[*] Created Y chunks (avg Z tokens per chunk)

[*] Running deduplication...
[*] Checking Y chunks against existing embeddings...
[OK] Deduplicated: X duplicates merged

[*] Storing graph relationships...
[OK] Created Y document-chunk relationships
[OK] Created Z email thread relationships
```

**What to look for:**
- ✅ Chunking applied to all documents
- ✅ Deduplication running (if enabled)
- ✅ Graph relationships created

#### 3f. Completion
```
[OK] Vectorstore initialized with X documents
[OK] HNSW graph indexing enabled (M=48, search_ef=100)
[OK] Vectorstore available with hybrid retrieval:
    - Primary: MMR (Maximal Marginal Relevance) for diverse results
    - Graph indexing: HNSW for efficient similarity search
    - Fallback: Similarity search
```

**Success indicators:**
- ✅ Document count matches expectations (2,000-15,000+)
- ✅ HNSW indexing enabled
- ✅ No critical errors in logs

---

## 🔍 Post-Rebuild Verification

### Step 1: Check Vectorstore Statistics
```bash
python check_vectorstore.py
```

**Expected Output:**
```
Total Documents: 5,000 - 15,000+

Source Types:
  sharepoint: 4,000 - 12,000 chunks (80-85%)
  web: 500 - 2,000 chunks (10-15%)
  email: 500 - 1,000 chunks (5-10%)

File Types:
  pdf: X chunks
  docx: Y chunks
  pptx: Z chunks
  xlsx: W chunks
  html: V chunks
```

### Step 2: Check Graph Relationships
```bash
python -c "import sqlite3; conn = sqlite3.connect('./data/graph_relations.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM documents'); docs = cursor.fetchone()[0]; cursor.execute('SELECT COUNT(*) FROM chunks'); chunks = cursor.fetchone()[0]; cursor.execute('SELECT COUNT(*) FROM relationships'); rels = cursor.fetchone()[0]; print(f'Documents: {docs}\\nChunks: {chunks}\\nRelationships: {rels}')"
```

**Expected Output:**
```
Documents: 2,000 - 5,000
Chunks: 5,000 - 15,000
Relationships: 10,000 - 30,000
```

### Step 3: Test Retrieval Quality

**Test Query 1: SharePoint Content**
```
Query: "What SOC 2 certifications does CloudFuze have?"
Expected: Find SOC 2 certificate documents from SharePoint
```

**Test Query 2: Email Threads**
```
Query: "What email discussions were there about migration issues?"
Expected: Find relevant email threads
```

**Test Query 3: Blog Content**
```
Query: "What blog posts discuss cloud migration best practices?"
Expected: Find relevant blog posts
```

### Step 4: Generate Ingestion Report
```bash
python -c "from app.ingest_reporter import generate_report; generate_report('./data/chroma_db')"
```

**Expected Report:**
- Total documents by source
- Total chunks by source
- File type breakdown
- Average chunk size
- Deduplication statistics
- Sample chunks with metadata

---

## ⚠️ Common Issues & Solutions

### Issue 1: Outlook Folder Not Found
```
[ERROR] Folder 'SentItems' not found
```
**Fix:** Change to `OUTLOOK_FOLDER_NAME=Sent Items` (with space)

### Issue 2: SharePoint Authentication Failed
```
[ERROR] Failed to get SharePoint access token
```
**Fix:** Verify Microsoft credentials in .env are correct

### Issue 3: Server Crashes During Ingestion
```
[ERROR] Memory error...
```
**Fix:** 
- Reduce batch size
- Process fewer files at once
- Increase system RAM
- Exclude large video/image folders

### Issue 4: Some Files Not Extracted
```
[WARNING] Skipping file: video.mp4 (unsupported)
```
**Expected:** Video files, images (except in PDFs) are skipped
**Action:** Normal behavior - only text-based content is extracted

### Issue 5: Slow Progress
**Symptom:** Ingestion taking hours
**Causes:**
- Large PDF files (100+ pages)
- Many PPTX files requiring Unstructured processing
- Slow network connection to SharePoint/Outlook
**Solution:** Normal - let it complete. Check logs for actual errors.

---

## 📊 Expected Results

### Ingestion Volume
| Source | Expected Documents | Expected Chunks |
|--------|-------------------|-----------------|
| SharePoint | 500 - 2,000 files | 4,000 - 12,000 chunks |
| Blogs | 100 - 500 posts | 500 - 2,000 chunks |
| Emails | 500 - 2,000 threads | 500 - 1,000 chunks |
| **TOTAL** | **1,000 - 4,500** | **5,000 - 15,000+** |

### File Type Breakdown
- PDF: 30-40% of SharePoint content
- DOCX: 25-35%
- XLSX: 10-15%
- PPTX: 5-10%
- HTML/Other: 10-20%

### Processing Time
| Phase | Duration |
|-------|----------|
| SharePoint | 30-60 minutes |
| Outlook | 20-40 minutes |
| Blogs | 10-20 minutes |
| Chunking | 10-15 minutes |
| Deduplication | 5-10 minutes |
| Graph Storage | 5 minutes |
| **TOTAL** | **1.5 - 2.5 hours** |

---

## ✅ Success Criteria

Rebuild is successful when:

1. ✅ All three sources ingested without critical errors
2. ✅ Total document count: 5,000 - 15,000+ chunks
3. ✅ SharePoint: 80-85% of total
4. ✅ Blogs: 10-15% of total
5. ✅ Emails: 5-10% of total
6. ✅ All file types present (PDF, DOCX, PPTX, XLSX)
7. ✅ HNSW graph indexing enabled
8. ✅ Graph relationships stored in SQLite
9. ✅ Test queries return relevant results
10. ✅ No "Folder not found" errors for Outlook

---

## 🎯 After Successful Rebuild

### 1. Test Chatbot
- Ask questions about SharePoint documents
- Ask about email discussions
- Ask about blog topics
- Verify accurate responses with source citations

### 2. Monitor Performance
- Check response times
- Verify result quality
- Test with various query types

### 3. Document Baseline
- Save document counts
- Note which folders/sources included
- Track ingestion stats for future comparison

---

## 🔄 Future Additions

Once initial rebuild is successful, you can add:
- **More emails**: Extend to `last_12_months` or `all_time`
- **Other folders**: Add Inbox, Archive, etc.
- **Other SharePoint sites**: Add additional sites
- **More blogs**: Extend pagination or add other sources

System supports **incremental updates** - won't rebuild everything!

---

## 📝 Notes

- **Deduplication**: Automatically handles duplicate content (85% similarity threshold)
- **Excluded Folders**: Screenshots, videos, and training recordings are skipped (configured in config.py)
- **Error Handling**: Non-critical errors (skipped files) won't stop ingestion
- **Incremental Updates**: After initial build, changes trigger smart rebuilds
- **Backups**: Always created before rebuild in `./data/backups/`

---

**Ready to start? Update your .env with the settings above and run:**

```bash
python server.py
```

**Monitor the logs and use this checklist to track progress!** 🚀

