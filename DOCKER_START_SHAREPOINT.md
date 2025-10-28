# Docker Commands for SharePoint Integration

## Prerequisites

Make sure your `.env` file has:
```bash
ENABLE_SHAREPOINT_SOURCE=true
INITIALIZE_VECTORSTORE=true
SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360
SHAREPOINT_START_PAGE=/SitePages/Multi%20User%20Golden%20Image%20Combinations.aspx
SHAREPOINT_MAX_DEPTH=3
```

## Step-by-Step Commands

### 1. Stop any running containers
```bash
docker-compose down
```

### 2. Rebuild Docker images (includes Chrome and Selenium)
```bash
docker-compose build
```

### 3. Start services
```bash
docker-compose up -d
```

### 4. Watch the logs to see SharePoint extraction
```bash
docker-compose logs -f backend
```

### 5. Check if SharePoint content was added
Look for these messages in the logs:
- `[*] Processing changed SharePoint content...`
- `[OK] Processed X SharePoint documents`
- `[OK] Successfully added new documents to vectorstore`

## Alternative: Run in foreground to see all output
```bash
docker-compose up
```

## Important Notes

### The First Run Will:
1. ✅ Start all services (backend, nginx, mongodb)
2. ✅ Extract 35 SharePoint pages using Selenium
3. ✅ Add them to your existing vectorstore (won't delete old data!)
4. ✅ Complete in 2-5 minutes depending on SharePoint access speed

### You'll see in the logs:
```
[*] SharePoint Selenium Extractor initialized
[*] Navigating to: https://cloudfuzecom.sharepoint.com/sites/DOC360/...
[⚠️] Authentication required!
[OK] Ready to extract content
[*] Depth 0: Processing 1 pages
   ✅ Extracted (1513 chars)
...
[OK] Extraction complete!
   Pages crawled: 35
   Documents created: 35
[*] Adding 35 new documents to existing vectorstore...
[OK] Successfully added new documents to vectorstore
```

## After Successful Extraction

### Test Your Chatbot
Open: http://localhost

Ask questions like:
- "Do we migrate app integration messages from Slack to Teams?"
- "What features are supported when migrating from Box?"
- "Can I migrate Slack channels into existing Teams?"

### Expected Results
**Before (without SharePoint):** Generic/unable to answer
**After (with SharePoint):** Specific, detailed answers with exact migration details

## Troubleshooting

### If SharePoint extraction fails:
1. Check authentication in SharePoint
2. Check logs: `docker-compose logs backend`
3. Verify `.env` has correct SharePoint URL and page

### If you see "Selenium not installed":
The Dockerfile now includes Chrome, but first build takes longer.

### To rebuild from scratch:
```bash
docker-compose down -v  # Removes volumes
docker-compose build --no-cache
docker-compose up -d
```

## Quick Commands Reference

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop everything
docker-compose down

# Rebuild (after changes)
docker-compose build && docker-compose up -d

# Check if services are running
docker-compose ps
```

## What Gets Updated

Your vectorstore will now contain:
- ✅ All existing data (web, PDFs, Excel, Word)
- ✅ Plus 35 NEW SharePoint documents
- **Total:** Everything you had + SharePoint knowledge base

## Time Estimate

- Docker build: 2-3 minutes (first time)
- SharePoint extraction: 2-5 minutes
- **Total:** ~5-8 minutes for first run

