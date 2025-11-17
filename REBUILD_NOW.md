# 🚀 START REBUILD NOW - Quick Guide

## ⚡ Quick Start (3 Steps)

### Step 1: Update Your `.env` File

Add or update these lines:

```bash
INITIALIZE_VECTORSTORE=true

ENABLE_WEB_SOURCE=true
ENABLE_SHAREPOINT_SOURCE=true
ENABLE_OUTLOOK_SOURCE=true

OUTLOOK_FOLDER_NAME=Sent Items
OUTLOOK_MAX_EMAILS=10000
OUTLOOK_DATE_FILTER=last_6_months

WEB_URL=https://cloudfuze.com/wp-json/wp/v2/posts?per_page=100
WEB_MAX_PAGES=100

SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360

# Enhanced features
ENABLE_DEDUPLICATION=true
ENABLE_UNSTRUCTURED=true
ENABLE_GRAPH_STORAGE=true
```

### Step 2: Backup (Optional but Recommended)

```bash
python scripts/backup_vectorstore.py
```

### Step 3: Start Rebuild

```bash
python server.py
```

---

## 📊 What to Expect

**Duration:** 1.5 - 2.5 hours

**Will ingest:**
- ✅ ALL blog posts (100-500+)
- ✅ ALL SharePoint files (1,000-5,000+)  
- ✅ ALL email threads from last 6 months (up to 10,000)

**Result:** 5,000 - 15,000+ document chunks

---

## 👀 Watch For

### Good Signs ✅
```
[OK] SharePoint access token obtained
[OK] Extracted file: Certificate.pdf
[OK] Fetched 250 emails
[OK] Total blog posts fetched: 150
[OK] Vectorstore initialized with 8,532 documents
```

### Bad Signs ❌
```
[ERROR] Folder 'SentItems' not found
→ Fix: Change to "Sent Items" (with space)

[ERROR] Failed to get SharePoint access token
→ Fix: Check Microsoft credentials

[ERROR] Memory error
→ Fix: Exclude large folders or add RAM
```

---

## ✅ Verify Success

After rebuild completes, run:

```bash
python check_vectorstore.py
```

Should show:
- **Total:** 5,000+ chunks
- **SharePoint:** 80-85%
- **Blogs:** 10-15%
- **Emails:** 5-10%

Then test in browser:
- "What SOC 2 certifications does CloudFuze have?"
- "Show me migration guides"
- "What did emails discuss about issues?"

---

**That's it! Your vectorstore will rebuild with everything.** 🎉

For detailed monitoring and troubleshooting, see `COMPLETE_REBUILD_CHECKLIST.md`

