# 🎛️ Individual Source Control System

## 📋 **Overview**

The CloudFuze Chatbot now supports **granular source control**, allowing you to selectively enable/disable individual data sources. This gives you precise control over what content gets indexed and when rebuilds occur.

---

## 🔧 **Environment Variables**

### **Master Control**
```bash
INITIALIZE_VECTORSTORE=true  # Enable vectorstore initialization
INITIALIZE_VECTORSTORE=false # Disable vectorstore initialization
```

### **Individual Source Controls**
```bash
# Web Content (CloudFuze Blog)
ENABLE_WEB_SOURCE=true   # Enable web content fetching
ENABLE_WEB_SOURCE=false  # Disable web content fetching

# PDF Documents
ENABLE_PDF_SOURCE=true   # Enable PDF processing
ENABLE_PDF_SOURCE=false  # Disable PDF processing

# Excel Files
ENABLE_EXCEL_SOURCE=true  # Enable Excel processing
ENABLE_EXCEL_SOURCE=false # Disable Excel processing

# Word Documents
ENABLE_DOC_SOURCE=true   # Enable Word document processing
ENABLE_DOC_SOURCE=false  # Disable Word document processing
```

### **Source-Specific Settings**
```bash
# Customize source locations and URLs
WEB_SOURCE_URL=https://www.cloudfuze.com/wp-json/wp/v2/posts?tags=412&per_page=100
PDF_SOURCE_DIR=./pdfs
EXCEL_SOURCE_DIR=./excel
DOC_SOURCE_DIR=./docs
```

---

## 🎯 **Usage Examples**

### **Example 1: Web + PDFs Only (Your Request)**
```bash
# Enable only web content and PDFs
ENABLE_WEB_SOURCE=true
ENABLE_PDF_SOURCE=true
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
INITIALIZE_VECTORSTORE=true
```

**Result**: Only web content and PDFs will be processed. Excel and Word documents will be ignored even if they exist in the directories.

### **Example 2: Web Content Only**
```bash
# Enable only web content
ENABLE_WEB_SOURCE=true
ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
INITIALIZE_VECTORSTORE=true
```

**Result**: Only CloudFuze blog content will be indexed. All local files will be ignored.

### **Example 3: Local Files Only**
```bash
# Enable only local files
ENABLE_WEB_SOURCE=false
ENABLE_PDF_SOURCE=true
ENABLE_EXCEL_SOURCE=true
ENABLE_DOC_SOURCE=true
INITIALIZE_VECTORSTORE=true
```

**Result**: Only local PDF, Excel, and Word files will be processed. Web content will be ignored.

### **Example 4: Disable All Sources**
```bash
# Disable all sources
ENABLE_WEB_SOURCE=false
ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
INITIALIZE_VECTORSTORE=true
```

**Result**: No content will be processed (fallback to web content for safety).

---

## 🚀 **How It Works**

### **1. Smart Change Detection**
The system only monitors **enabled sources** for changes:

```python
# Only check enabled sources
enabled_sources = current_metadata.get("enabled_sources", [])
for source in enabled_sources:
    if stored_metadata.get(source) != current_metadata.get(source):
        return True  # Rebuild needed
```

### **2. Selective Processing**
Only enabled sources are processed during rebuilds:

```python
# Web content (if enabled)
if ENABLE_WEB_SOURCE:
    # Process web content
    
# PDFs (if enabled)
if ENABLE_PDF_SOURCE and os.path.exists(PDF_SOURCE_DIR):
    # Process PDF files
    
# Excel (if enabled)
if ENABLE_EXCEL_SOURCE and os.path.exists(EXCEL_SOURCE_DIR):
    # Process Excel files
    
# Word docs (if enabled)
if ENABLE_DOC_SOURCE and os.path.exists(DOC_SOURCE_DIR):
    # Process Word documents
```

### **3. Cost Optimization**
- **No unnecessary API calls** for disabled sources
- **Faster rebuilds** when fewer sources are enabled
- **Reduced storage** when processing fewer documents

---

## 📊 **Configuration Examples**

### **Docker Compose Configuration**
```yaml
environment:
  - INITIALIZE_VECTORSTORE=true
  - ENABLE_WEB_SOURCE=true
  - ENABLE_PDF_SOURCE=true
  - ENABLE_EXCEL_SOURCE=false
  - ENABLE_DOC_SOURCE=false
```

### **Environment File (.env)**
```bash
# Master control
INITIALIZE_VECTORSTORE=true

# Source controls
ENABLE_WEB_SOURCE=true
ENABLE_PDF_SOURCE=true
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false

# Optional: Custom paths
PDF_SOURCE_DIR=./my_pdfs
EXCEL_SOURCE_DIR=./my_excel_files
```

### **Production Configuration**
```bash
# Production: Web + PDFs only
INITIALIZE_VECTORSTORE=true
ENABLE_WEB_SOURCE=true
ENABLE_PDF_SOURCE=true
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
```

---

## 🔍 **Monitoring & Debugging**

### **Check Current Status**
```bash
python manage_vectorstore.py status
```

**Output Example:**
```
============================================================
VECTORSTORE STATUS CHECK
============================================================
Vectorstore exists: true
Document count: 150
Last updated: 2025-10-24T10:30:00
Blog URL: https://www.cloudfuze.com/wp-json/wp/v2/posts?tags=412&per_page=100
Enabled sources: web, pdfs
============================================================
```

### **Manual Rebuild with Selected Sources**
```bash
python manage_vectorstore.py rebuild
```

**Output Example:**
```
============================================================
MANUAL VECTORSTORE REBUILD
============================================================
⚠️  WARNING: This will cost $8-12 in OpenAI API calls!
Building vectorstore with sources: web, pdf
Enabled sources: Web content (CloudFuze blog), PDFs (5 files)
Building knowledge base with enabled sources only...
Total documents indexed: 150
✅ Vectorstore rebuilt successfully!
```

---

## 💡 **Best Practices**

### **1. Development Environment**
```bash
# Fast development setup
INITIALIZE_VECTORSTORE=true
ENABLE_WEB_SOURCE=true
ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
```

### **2. Production Environment**
```bash
# Full production setup
INITIALIZE_VECTORSTORE=true
ENABLE_WEB_SOURCE=true
ENABLE_PDF_SOURCE=true
ENABLE_EXCEL_SOURCE=true
ENABLE_DOC_SOURCE=true
```

### **3. Cost-Conscious Setup**
```bash
# Minimal cost setup
INITIALIZE_VECTORSTORE=true
ENABLE_WEB_SOURCE=true
ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
```

### **4. Testing Setup**
```bash
# Test with specific sources
INITIALIZE_VECTORSTORE=true
ENABLE_WEB_SOURCE=false
ENABLE_PDF_SOURCE=true
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
```

---

## 🚨 **Important Notes**

### **1. Change Detection**
- Only **enabled sources** are monitored for changes
- Disabled sources are **completely ignored**
- Changes in disabled sources **will not trigger rebuilds**

### **2. Cost Management**
- **Web content**: ~$8-12 per rebuild
- **PDFs**: ~$2-4 per rebuild (depending on file count)
- **Excel**: ~$1-3 per rebuild
- **Word docs**: ~$1-3 per rebuild

### **3. Performance**
- **Fewer sources** = faster rebuilds
- **Fewer sources** = smaller vectorstore
- **Fewer sources** = faster queries

### **4. Fallback Behavior**
- If **no sources are enabled**, system falls back to web content
- If **web is disabled** but other sources are enabled, only local files are processed
- If **all sources are disabled**, web content is used as fallback

---

## 🎯 **Your Specific Use Case**

For your request (Web + PDFs only):

```bash
# Set these environment variables
INITIALIZE_VECTORSTORE=true
ENABLE_WEB_SOURCE=true
ENABLE_PDF_SOURCE=true
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
```

**Result:**
- ✅ **Web content** will be fetched and processed
- ✅ **PDF files** in `./pdfs/` will be processed
- ❌ **Excel files** will be ignored (even if they exist)
- ❌ **Word documents** will be ignored (even if they exist)
- 🔄 **Only web and PDF changes** will trigger rebuilds
- 💰 **Reduced cost** (~$10-15 per rebuild instead of $16-20)

This gives you exactly what you requested: **selective source control** with only web data and PDFs being monitored and updated! 🚀
