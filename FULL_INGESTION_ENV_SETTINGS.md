# 🚀 Full Ingestion .env Settings

## Copy These Settings to Your `.env` File

```bash
# ============================================================================
# VECTORSTORE INITIALIZATION
# ============================================================================
INITIALIZE_VECTORSTORE=true

# ============================================================================
# SOURCE CONFIGURATION - Enable All Sources
# ============================================================================
ENABLE_WEB_SOURCE=true
ENABLE_SHAREPOINT_SOURCE=true
ENABLE_OUTLOOK_SOURCE=true

ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false

# ============================================================================
# BLOG/WEB CONFIGURATION - All Blog Posts
# ============================================================================
WEB_URL=https://cloudfuze.com/wp-json/wp/v2/posts?per_page=100
WEB_START_PAGE=1
WEB_MAX_PAGES=100

# ============================================================================
# SHAREPOINT CONFIGURATION - All Files
# ============================================================================
SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360

# ============================================================================
# OUTLOOK CONFIGURATION - All Threads from Last 6 Months
# ============================================================================
OUTLOOK_USER_EMAIL=presales@cloudfuze.com
OUTLOOK_FOLDER_NAME=Sent Items
OUTLOOK_MAX_EMAILS=10000
OUTLOOK_DATE_FILTER=last_6_months

# ============================================================================
# OPENAI API KEY (Keep your existing value)
# ============================================================================
OPENAI_API_KEY=sk-your-actual-key-here

# ============================================================================
# MICROSOFT CREDENTIALS (Keep your existing values)
# ============================================================================
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret
MICROSOFT_TENANT=your_tenant_id

# ============================================================================
# ENHANCED INGESTION SETTINGS
# ============================================================================
CHUNK_TARGET_TOKENS=800
CHUNK_OVERLAP_TOKENS=200
CHUNK_MIN_TOKENS=150

ENABLE_DEDUPLICATION=true
DEDUP_THRESHOLD=0.85

ENABLE_UNSTRUCTURED=true
ENABLE_OCR=true
OCR_LANGUAGE=eng

GRAPH_DB_PATH=./data/graph_relations.db
ENABLE_GRAPH_STORAGE=true
```

---

## ⚠️ Important Notes

### 1. **Outlook Folder Name**
Your `.env` shows `OUTLOOK_FOLDER_NAME=SentItems` but standard Outlook folder name is:
```bash
OUTLOOK_FOLDER_NAME=Sent Items  # With space
```

### 2. **Email Limit Increased**
Changed from:
```bash
OUTLOOK_MAX_EMAILS=500  # OLD - May miss threads
```
To:
```bash
OUTLOOK_MAX_EMAILS=10000  # NEW - Get all threads from last 6 months
```

### 3. **All Sources Enabled**
```bash
ENABLE_WEB_SOURCE=true        # ✅ All blog posts
ENABLE_SHAREPOINT_SOURCE=true # ✅ All SharePoint files
ENABLE_OUTLOOK_SOURCE=true    # ✅ All email threads (6 months)
```

---

## 📊 What Will Be Ingested

| Source | Content | Expected Count |
|--------|---------|----------------|
| **Blogs** | All posts from cloudfuze.com | 100-500+ posts |
| **SharePoint** | All files in DOC360 site | 1000-5000+ files |
| **Emails** | All threads from last 6 months | Up to 10,000 emails |

**Total Expected:** 2,000 - 15,000+ documents (chunked into many more embeddings)

---

## 🚀 Steps to Execute

### Step 1: Update Your `.env` File
```bash
# Add/update these settings in your .env file
INITIALIZE_VECTORSTORE=true
ENABLE_WEB_SOURCE=true
ENABLE_SHAREPOINT_SOURCE=true
ENABLE_OUTLOOK_SOURCE=true
OUTLOOK_FOLDER_NAME=Sent Items
OUTLOOK_MAX_EMAILS=10000
```

### Step 2: Restart Server
```bash
python server.py
```

### Step 3: Monitor Progress
Watch the server logs for:
```
============================================================
>> INITIALIZING CF-CHATBOT KNOWLEDGE BASE
============================================================
[*] Processing SharePoint content...
[*] Processing Outlook emails...
[*] Processing web content (blogs)...
```

### Step 4: Verify Completion
Look for:
```
[OK] Vectorstore initialized with X documents
```

---

## ⏱️ Expected Time

Based on content volume:
- **SharePoint (1000+ files):** 30-60 minutes
- **Emails (500-10,000 threads):** 20-40 minutes
- **Blogs (100-500 posts):** 10-20 minutes

**Total:** 1-2 hours for full ingestion

---

## 🔍 After Ingestion - Verify

Run this to check what was ingested:
```bash
python check_vectorstore.py
```

Expected output:
```
Total Documents: 5000-15000+
└─ SharePoint: 4000-12000 chunks
└─ Blogs: 500-2000 chunks
└─ Emails: 500-1000 chunks
```

---

## 🐛 Troubleshooting

### Issue: "Folder 'SentItems' not found"
**Fix:** Change to `OUTLOOK_FOLDER_NAME=Sent Items` (with space)

### Issue: Server is slow/hanging
**Reason:** Processing large files (PDFs, videos)
**Solution:** Normal - wait for completion or exclude large folders

### Issue: Out of memory
**Reason:** Processing too many large files at once
**Solution:** Reduce batch size or add more RAM

---

## ✅ Ready to Start?

Once you update your `.env` file with the settings above and restart the server, the full ingestion will begin automatically!

