# 🔧 Environment File Setup Guide

## 📋 **What to Add to Your `.env` File**

Create a `.env` file in your project root with these variables:

```bash
# ===========================================
# REQUIRED VARIABLES (Fill these in)
# ===========================================

# OpenAI API Key
OPENAI_API_KEY=your_actual_openai_api_key_here

# Microsoft OAuth Configuration  
MICROSOFT_CLIENT_ID=your_actual_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_actual_microsoft_client_secret
MICROSOFT_TENANT=cloudfuze.com

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=your_actual_langfuse_public_key
LANGFUSE_SECRET_KEY=your_actual_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

# ===========================================
# VECTORSTORE CONTROL
# ===========================================

# Enable vectorstore initialization
INITIALIZE_VECTORSTORE=true

# ===========================================
# INDIVIDUAL SOURCE CONTROL
# ===========================================
# Your specific configuration: Web + PDFs only

# Web content (CloudFuze blog) - ENABLED
ENABLE_WEB_SOURCE=true

# PDF documents - ENABLED  
ENABLE_PDF_SOURCE=true

# Excel files - DISABLED
ENABLE_EXCEL_SOURCE=false

# Word documents - DISABLED
ENABLE_DOC_SOURCE=false

# ===========================================
# OPTIONAL SETTINGS (Defaults work fine)
# ===========================================

# Source directories (optional - defaults work)
PDF_SOURCE_DIR=./pdfs
EXCEL_SOURCE_DIR=./excel
DOC_SOURCE_DIR=./docs

# Web source URL (optional - default works)
WEB_SOURCE_URL=https://www.cloudfuze.com/wp-json/wp/v2/posts?tags=412&per_page=100

# MongoDB settings (optional - defaults work)
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories
```

## 🎯 **Your Specific Configuration**

For **Web + PDFs only** (as you requested), make sure these are set:

```bash
# Enable only web content and PDFs
ENABLE_WEB_SOURCE=true
ENABLE_PDF_SOURCE=true
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
INITIALIZE_VECTORSTORE=true
```

## 📝 **Step-by-Step Setup**

1. **Create `.env` file** in your project root
2. **Copy the template above** into your `.env` file
3. **Replace the placeholder values** with your actual API keys
4. **Save the file**
5. **Restart your services**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## ✅ **What This Configuration Does**

- ✅ **Web Content**: Fetches CloudFuze blog posts
- ✅ **PDF Files**: Processes PDFs in `./pdfs/` directory
- ❌ **Excel Files**: Completely ignored
- ❌ **Word Documents**: Completely ignored
- 🔄 **Smart Rebuilds**: Only rebuilds when web content or PDFs change
- 💰 **Cost Savings**: ~$10-15 per rebuild instead of $16-20

## 🚨 **Important Notes**

1. **Replace placeholder values** with your actual API keys
2. **Keep the boolean values** as `true`/`false` (no quotes)
3. **Make sure** `INITIALIZE_VECTORSTORE=true` is set
4. **Your specific config**: Web + PDFs only as requested

## 🔍 **Testing Your Configuration**

After setting up your `.env` file, test it:

```bash
python test_source_control.py
```

This will show you exactly which sources are enabled and what will be processed.
