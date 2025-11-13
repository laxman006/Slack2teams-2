@echo off
echo ========================================
echo Creating .env file
echo ========================================
echo.

if exist .env (
    echo [WARNING] .env file already exists!
    echo Press Ctrl+C to cancel or
    pause
    echo Creating backup...
    copy .env .env.backup >nul
    echo Backup saved to .env.backup
    echo.
)

echo Creating .env file with your configuration...
echo.

(
echo # OpenAI API Configuration
echo OPENAI_API_KEY=your_openai_api_key_here
echo.
echo # Microsoft OAuth Configuration
echo MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
echo MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here
echo MICROSOFT_TENANT=cloudfuze.com
echo.
echo # Langfuse Configuration ^(Observability ^& Prompt Management^)
echo # NOTE: Prompt fetching is DISABLED - using config.py SYSTEM_PROMPT
echo # These keys are only used for observability/tracing
echo LANGFUSE_PUBLIC_KEY=pk-lf-200cf28a-10e2-4f57-8d21-5b56aae7ba78
echo LANGFUSE_SECRET_KEY=sk-lf-9e666df7-d242-49f0-9365-f4814b0b3eb9
echo LANGFUSE_HOST=https://cloud.langfuse.com
echo.
echo # MongoDB Configuration
echo MONGODB_URL=mongodb://localhost:27017
echo MONGODB_DATABASE=slack2teams
echo MONGODB_CHAT_COLLECTION=chat_histories
echo.
echo # Vectorstore Configuration
echo INITIALIZE_VECTORSTORE=false
echo.
echo # Data Source Configuration
echo ENABLE_WEB_SOURCE=false
echo ENABLE_PDF_SOURCE=false
echo ENABLE_EXCEL_SOURCE=false
echo ENABLE_DOC_SOURCE=false
echo ENABLE_SHAREPOINT_SOURCE=false
echo.
echo # SharePoint Configuration
echo SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360
echo SHAREPOINT_START_PAGE=
echo SHAREPOINT_MAX_DEPTH=999
echo SHAREPOINT_EXCLUDE_FILES=true
) > .env

echo.
echo [SUCCESS] .env file created!
echo.
echo ========================================
echo IMPORTANT: Edit the .env file and add:
echo ========================================
echo 1. Your OPENAI_API_KEY
echo 2. Your MICROSOFT_CLIENT_ID
echo 3. Your MICROSOFT_CLIENT_SECRET
echo.
echo Langfuse keys are already filled in.
echo.
echo Opening .env file in notepad...
notepad .env
echo.
echo After editing, save and run: python server.py
echo.
pause

