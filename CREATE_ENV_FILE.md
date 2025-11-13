# Create Your .env File

Your `.env` file is missing. Follow these steps:

## Step 1: Create the .env file

**Option A: Using Command Line (PowerShell)**
```powershell
# Create the file
New-Item -Path .env -ItemType File

# Open in notepad
notepad .env
```

**Option B: Using File Explorer**
1. Right-click in the project folder
2. New → Text Document
3. Name it `.env` (with the dot at the start, no .txt extension)

---

## Step 2: Add Your Configuration

Copy and paste this into your `.env` file:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here
MICROSOFT_TENANT=cloudfuze.com

# Langfuse Configuration (Observability & Prompt Management)
# NOTE: Prompt fetching is DISABLED - using config.py SYSTEM_PROMPT
# These keys are only used for observability/tracing
LANGFUSE_PUBLIC_KEY=pk-lf-200cf28a-10e2-4f57-8d21-5b56aae7ba78
LANGFUSE_SECRET_KEY=sk-lf-9e666df7-d242-49f0-9365-f4814b0b3eb9
LANGFUSE_HOST=https://cloud.langfuse.com

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories

# Vectorstore Configuration
INITIALIZE_VECTORSTORE=false

# Data Source Configuration
ENABLE_WEB_SOURCE=false
ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false
ENABLE_SHAREPOINT_SOURCE=false

# SharePoint Configuration
SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360
SHAREPOINT_START_PAGE=
SHAREPOINT_MAX_DEPTH=999
SHAREPOINT_EXCLUDE_FILES=true
```

---

## Step 3: Fill in Your Actual Values

Replace these placeholders with your real values:
- `OPENAI_API_KEY` - Your OpenAI API key
- `MICROSOFT_CLIENT_ID` - Your Microsoft app client ID
- `MICROSOFT_CLIENT_SECRET` - Your Microsoft app secret

**Note:** Langfuse keys are already filled in (you shared them earlier)

---

## Step 4: Save and Test

1. Save the `.env` file
2. Run your server: `python server.py`
3. You should see:
   ```
   [OK] Langfuse prompt manager initialized
   [INFO] Langfuse prompt fetching DISABLED - using config.py SYSTEM_PROMPT only
   [INFO] Langfuse observability (tracing/logging) remains ACTIVE
   ```

---

## What Changed?

✅ **Langfuse prompt fetching is now DISABLED**
   - Your chatbot uses `config.py` SYSTEM_PROMPT
   - Edit `config.py` line 22 to change the prompt
   - Changes take effect after server restart

✅ **Langfuse observability is still ACTIVE**
   - All chat interactions are logged
   - Tracing and analytics work normally
   - You can view traces in Langfuse dashboard

---

## To Re-enable Langfuse Prompts Later

Edit `app/prompt_manager.py` line 18:
```python
ENABLE_LANGFUSE_PROMPTS = True  # Change False to True
```

---

## Security Reminder

⚠️ **IMPORTANT:** The Langfuse keys you shared earlier are now exposed!

**After creating .env, rotate your keys:**
1. Go to: https://cloud.langfuse.com
2. Settings → API Keys
3. Delete the exposed keys
4. Generate new keys
5. Update them in your `.env` file

