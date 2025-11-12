# Vectorstore Rebuild Guide - With Proper Tags & Metadata

## 🎯 What This Rebuild Will Do

✅ **Fix corruption** - Resolves the ChromaDB index errors  
✅ **Proper tags** - Assigns hierarchical tags for better retrieval  
✅ **Fresh content** - Gets latest blog posts and SharePoint documents  
✅ **Full metadata** - Includes URLs, titles, folder paths, download links  

---

## 📋 Tags & Metadata Structure

### Blog Posts
```
tag: "blog"
source: "cloudfuze_blog"
metadata:
  - post_title: "Box to SharePoint Migration Guide"
  - post_url: "https://cloudfuze.com/box-to-sharepoint/"
  - post_slug: "box-to-sharepoint"
  - is_blog_post: true
```

### SharePoint Documents  
```
tag: "sharepoint/Documentation/Migration Guides"  # Hierarchical!
source: "cloudfuze_doc360"
metadata:
  - folder_path: "Documentation > Migration Guides"
  - file_name: "OneDrive_Migration_Guide.pdf"
  - file_url: "https://cloudfuzecom.sharepoint.com/..."
  - is_certificate: true (for certs)
  - download_url: "..." (for downloadable files)
```

### PDFs, Excel, Word
```
tag: "pdf" | "excel" | "doc"
metadata:
  - source: filename
  - page_number: X (for PDFs)
```

---

## 🚀 Step-by-Step Rebuild Process

### Step 1: Backup Current Vectorstore

**Windows (PowerShell):**
```powershell
Copy-Item -Recurse data\chroma_db "data\chroma_db_backup_manual_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
```

**Linux/Mac (Bash):**
```bash
cp -r data/chroma_db "data/chroma_db_backup_manual_$(date +%Y%m%d_%H%M%S)"
```

### Step 2: Verify Environment Settings

Check your `.env` file:
```bash
# Required sources
ENABLE_WEB_SOURCE=true              # Blog posts
ENABLE_SHAREPOINT_SOURCE=true       # SharePoint docs

# Optional sources (set to true if you have them)
ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false

# SharePoint configuration
SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360
SHAREPOINT_START_PAGE=              # Empty = entire Documents library
SHAREPOINT_MAX_DEPTH=999            # Unlimited depth
```

### Step 3: Run the Rebuild

```powershell
python manage_vectorstore.py rebuild
```

**Expected output:**
```
============================================================
MANUAL VECTORSTORE REBUILD
============================================================
⚠️  WARNING: This will cost $16-20 in OpenAI API calls!
This will fetch and process all blog content from CloudFuze.

Do you want to continue? (yes/no): yes

Starting vectorstore rebuild...
[*] Building vectorstore with sources: web, sharepoint
[*] Fetching blog posts from CloudFuze...
[OK] Loaded 1330 blog posts into 15000+ chunks with full metadata
[*] Processing SharePoint content...
[OK] Processed 500 SharePoint documents
✅ Vectorstore rebuilt successfully!
Total documents: 15500+
Timestamp: 2025-11-11T...
```

**Time estimate:** 10-30 minutes depending on content volume

### Step 4: Verify the Rebuild

```powershell
python verify_rebuild.py
```

**Expected output:**
```
============================================================
VECTORSTORE VERIFICATION
============================================================

✅ Total Documents: 15500

============================================================
📊 DOCUMENTS BY TAG
============================================================
  blog                                               : 13000 docs (83.9%)
  sharepoint/Documentation                           :   500 docs ( 3.2%)
  sharepoint/Certificates                            :   200 docs ( 1.3%)
  ...

============================================================
📂 DOCUMENTS BY SOURCE
============================================================
  cloudfuze_blog                 : 13000 docs (83.9%)
  cloudfuze_doc360              :  2500 docs (16.1%)

============================================================
📁 SHAREPOINT ANALYSIS
============================================================
  SharePoint documents: 2500
  SharePoint unique folders: 25
  SharePoint top-level folders: 5

  Top-level SharePoint folders:
    • Certificates
    • Documentation
    • Guides
    • Policies
    • Videos

✅ VERIFICATION COMPLETE
```

### Step 5: Restart Your Server

```powershell
# Stop current server (Ctrl+C)
# Then start fresh:
python server.py
```

### Step 6: Test Retrieval

Test a query to see the improved retrieval:
```powershell
# In a new terminal
curl -X POST http://localhost:8002/chat/test -H "Content-Type: application/json" -d "{\"question\": \"Download SOC 2 certificate\", \"session_id\": \"test\"}"
```

---

## 📊 What to Check After Rebuild

### 1. Document Counts
- ✅ Blog posts: Should be 1300-1500 posts (13000+ chunks)
- ✅ SharePoint: Should have documents from your SharePoint site
- ✅ No "unknown" tags

### 2. Tag Distribution
- ✅ Blog posts tagged as "blog"
- ✅ SharePoint docs with hierarchical tags like "sharepoint/Documentation/..."
- ✅ Each document has proper source metadata

### 3. SharePoint Folders
- ✅ Certificates folder indexed
- ✅ Documentation folder indexed
- ✅ Policy documents indexed
- ✅ Migration guides indexed

### 4. Test Queries
```
✅ "What is CloudFuze?" → Should use blog posts
✅ "Download SOC 2 certificate" → Should use SharePoint
✅ "OneDrive migration" → Should use both blog + SharePoint
```

---

## 🔧 Troubleshooting

### Issue: Rebuild Fails

**Check:**
1. Internet connection (needs to fetch blog posts)
2. SharePoint authentication in `.env`
3. OpenAI API key is valid and has credits

**Solution:**
```powershell
# Clear and rebuild
python manage_vectorstore.py clear
python manage_vectorstore.py rebuild
```

### Issue: No SharePoint Documents

**Check `.env`:**
```bash
ENABLE_SHAREPOINT_SOURCE=true  # Must be true!
```

**Verify SharePoint auth:**
```powershell
python test_sharepoint_extraction.py
```

### Issue: Still Getting "I Don't Have Information"

**Possible reasons:**
1. ❌ Content about that topic doesn't exist in blog/SharePoint
2. ❌ Keywords not detected properly (need keyword enhancement)
3. ❌ Relevant docs scored low (check similarity scores in debug logs)

**Check what was retrieved:**
- Look at server terminal logs: `[DEBUG] Documents by tag: {...}`
- If no relevant docs retrieved → content doesn't exist
- If docs retrieved but bot says "I don't have" → docs don't answer the specific question

---

## 💡 After Rebuild Success

### What's Fixed:
✅ Corruption resolved  
✅ Latest content indexed  
✅ Proper tags assigned  
✅ Hierarchical SharePoint structure  
✅ Full metadata for all documents  

### What's NOT Fixed:
❌ Missing content (if blog/SharePoint don't have it)  
❌ Keyword detection for features like "logs", "reporting"  
❌ Query relevance issues  

### Next Steps (Optional Improvements):

1. **Enhance Keyword Detection**
   - Add feature keywords: logs, reporting, permissions, security
   - Better matching for specific features
   - Improved retrieval accuracy

2. **Add Missing Content**
   - Create blog posts about missing topics
   - Add SharePoint docs for technical features
   - Update documentation

3. **Monitor Performance**
   - Check Langfuse traces
   - Review "I don't have information" responses
   - Identify content gaps

---

## 📝 Summary

| Step | Command | Purpose |
|------|---------|---------|
| 1. Backup | `Copy-Item -Recurse data\chroma_db ...` | Safety backup |
| 2. Rebuild | `python manage_vectorstore.py rebuild` | Fix corruption + fresh index |
| 3. Verify | `python verify_rebuild.py` | Check tags/metadata |
| 4. Restart | `python server.py` | Load fresh vectorstore |
| 5. Test | Test queries in UI | Verify improved retrieval |

**Total time:** 15-45 minutes  
**Cost:** $16-20 in OpenAI embeddings  
**Result:** Fresh, properly tagged vectorstore with latest content!

---

## 🎯 Expected Improvements

After rebuilding with proper tags:

✅ **Better retrieval** - Intent-based filtering uses tags  
✅ **SharePoint integration** - Certificates, policies properly tagged  
✅ **Blog content** - Latest posts with full metadata  
✅ **No corruption** - Fresh, clean index  
✅ **Hierarchical structure** - SharePoint folders organized  

**Still need to address separately:**
- Missing content topics (add to blog/SharePoint)
- Feature keyword detection (enhance code)
- Content quality (update existing docs)

