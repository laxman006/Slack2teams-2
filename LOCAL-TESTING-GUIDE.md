# Local Testing Guide - Microsoft Login

This guide will help you test the Microsoft login functionality locally.

## Prerequisites

- Python 3.8 or higher
- Git
- Modern web browser (Chrome, Edge, Firefox)
- Azure AD application credentials (Client ID & Secret)

## Step 1: Pull the Latest Code

```bash
# If you haven't cloned yet
git clone <your-repo-url>
cd Slack2teams-2

# If already cloned, pull latest changes
git pull origin main
```

## Step 2: Set Up Python Environment

### Windows (PowerShell)

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activating again
.\venv\Scripts\Activate.ps1
```

### Windows (Command Prompt)

```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat
```

### Linux/Mac

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you encounter any issues, install packages individually:

```bash
pip install fastapi uvicorn httpx python-dotenv
pip install langchain langchain-openai langchain-community
pip install chromadb motor pymongo
pip install langfuse beautifulsoup4 pandas openpyxl pypdf
```

## Step 4: Configure Environment Variables

1. **Copy the example environment file:**

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Windows (Command Prompt)
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

2. **Edit `.env` file** and add your credentials:

```env
# Required for Microsoft Login
MICROSOFT_CLIENT_ID=63bd4522-368b-4bd7-a84d-9c7f205cd2a6
MICROSOFT_CLIENT_SECRET=<your-actual-secret-from-azure>
MICROSOFT_TENANT=cloudfuze.com

# Required for Chatbot
OPENAI_API_KEY=<your-openai-api-key>

# Required for Langfuse
LANGFUSE_PUBLIC_KEY=<your-langfuse-public-key>
LANGFUSE_SECRET_KEY=<your-langfuse-secret-key>
LANGFUSE_HOST=https://cloud.langfuse.com

# Optional - MongoDB (will use local if not changed)
MONGODB_URL=mongodb://localhost:27017
```

**Where to get these credentials:**

- **MICROSOFT_CLIENT_SECRET**: 
  - Go to [Azure Portal](https://portal.azure.com)
  - Navigate to: Azure Active Directory → App Registrations → Your App → Certificates & Secrets
  - Click "New client secret"
  - Copy the **Value** (not the Secret ID)
  
- **OPENAI_API_KEY**:
  - Go to [OpenAI Platform](https://platform.openai.com/api-keys)
  - Click "Create new secret key"
  
- **LANGFUSE_PUBLIC_KEY & LANGFUSE_SECRET_KEY**:
  - Go to your [Langfuse instance](https://cloud.langfuse.com)
  - Navigate to Settings → API Keys
  - Create new API key or copy existing ones

## Step 5: Set Up MongoDB (Choose One Option)

### Option A: Use Local MongoDB (Recommended for Testing)

1. **Install MongoDB:**
   - **Windows**: Download from [MongoDB Download Center](https://www.mongodb.com/try/download/community)
   - **Mac**: `brew install mongodb-community`
   - **Linux**: Follow [official guide](https://docs.mongodb.com/manual/administration/install-on-linux/)

2. **Start MongoDB:**
   ```bash
   # Windows (as service)
   net start MongoDB
   
   # Mac
   brew services start mongodb-community
   
   # Linux
   sudo systemctl start mongod
   ```

3. **Verify MongoDB is running:**
   ```bash
   # Check if MongoDB is listening on port 27017
   # Windows
   netstat -ano | findstr :27017
   
   # Linux/Mac
   lsof -i :27017
   ```

### Option B: Use MongoDB Atlas (Cloud)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free cluster
3. Get connection string
4. Update `.env`:
   ```env
   MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### Option C: Skip MongoDB (Use JSON Storage)

The app will automatically fall back to JSON-based storage if MongoDB is unavailable. No action needed.

## Step 6: Run Diagnostic Tests

Run the authentication test script:

```bash
python test_auth.py
```

**Expected Output:**
```
============================================================
Microsoft OAuth Configuration Test
Generated at: 2024-XX-XX XX:XX:XX
============================================================

1. Environment Variables
------------------------------------------------------------
   ✅ MICROSOFT_CLIENT_ID: Set (63bd4522...)
   ✅ MICROSOFT_CLIENT_SECRET: Set (***hidden***)
   ✅ MICROSOFT_TENANT: cloudfuze.com
   ✅ OPENAI_API_KEY: Set (***hidden***)
   ✅ LANGFUSE_PUBLIC_KEY: Set
   ✅ LANGFUSE_SECRET_KEY: Set
   ✅ MONGODB_URL: mongodb://localhost:27017

2. Azure AD Connectivity
------------------------------------------------------------
   ✅ Azure AD endpoint reachable (tenant: cloudfuze.com)

3. Backend Connectivity
------------------------------------------------------------
   ❌ Backend not reachable at http://localhost:8002
   💡 Start backend with: python server.py

4. MongoDB Connectivity
------------------------------------------------------------
   ✅ MongoDB is reachable at mongodb://localhost:27017

5. Frontend Configuration
------------------------------------------------------------
   ✅ MICROSOFT_CLIENT_ID found in login.html
   ✅ Tenant 'cloudfuze.com' found in login.html
   ✅ index.html found

6. Recommendations
------------------------------------------------------------
Action Items:
   1. Start the backend server
```

## Step 7: Start the Backend Server

Open a terminal and run:

```bash
# Make sure virtual environment is activated
# You should see (venv) in your terminal prompt

# Start the server
python server.py
```

**Expected Output:**
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
✅ MongoDB memory storage initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
```

**Keep this terminal open!** The server needs to run continuously.

## Step 8: Open Frontend in Browser

1. **Open a new terminal** (keep server running in the first one)

2. **Start a simple HTTP server for frontend:**

   ```bash
   # Python 3
   python -m http.server 8003
   
   # Or use Python 2
   python -m SimpleHTTPServer 8003
   ```

3. **Open browser and navigate to:**
   ```
   http://localhost:8003/login.html
   ```

## Step 9: Test Microsoft Login

1. Click "Sign in with Microsoft" button
2. You'll be redirected to Microsoft login page
3. Sign in with your CloudFuze email (`user@cloudfuze.com`)
4. Accept permissions if prompted
5. You should be redirected back to the app

### Troubleshooting Login Issues

**Open Browser Console (F12)** and check for errors:

**Good Signs:**
```javascript
Login page initialized
OAuth code received, processing...
```

**Bad Signs:**
```javascript
Code verifier not found
Failed to exchange code for token
Access denied
```

## Step 10: Monitor Backend Logs

In the terminal where `server.py` is running, you should see:

**Successful Login:**
```
INFO:     127.0.0.1:XXXXX - "POST /auth/microsoft/callback HTTP/1.1" 200 OK
```

**Failed Login:**
```
INFO:     127.0.0.1:XXXXX - "POST /auth/microsoft/callback HTTP/1.1" 400 Bad Request
```

## Common Issues and Solutions

### Issue 1: "MICROSOFT_CLIENT_SECRET not found"

**Solution:**
```bash
# Check if .env file exists
ls -la .env  # Linux/Mac
dir .env     # Windows

# Verify environment variables are loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('MICROSOFT_CLIENT_SECRET'))"
```

### Issue 2: "Port 8002 already in use"

**Solution:**
```bash
# Find process using port 8002
# Windows
netstat -ano | findstr :8002
taskkill /PID <process_id> /F

# Linux/Mac
lsof -ti:8002 | xargs kill -9

# Or use a different port
uvicorn server:app --host 0.0.0.0 --port 8005
```

### Issue 3: "ModuleNotFoundError"

**Solution:**
```bash
# Reinstall requirements
pip install -r requirements.txt

# Or install missing package individually
pip install <package_name>
```

### Issue 4: "MongoDB connection failed"

**Solutions:**

1. **Use JSON storage instead** (automatic fallback)
2. **Check MongoDB is running:**
   ```bash
   # Windows
   net start MongoDB
   
   # Mac
   brew services start mongodb-community
   
   # Linux
   sudo systemctl start mongod
   ```
3. **Or use MongoDB Atlas** (see Step 5, Option B)

### Issue 5: "Code verifier not found"

**Solution:**
Update `login.html` line 253 to use `localStorage`:

```javascript
// Change from:
sessionStorage.setItem('code_verifier', codeVerifier);

// To:
localStorage.setItem('code_verifier', codeVerifier);
```

Also update lines 378 and 419 similarly.

### Issue 6: "CORS policy error"

**Solution:**
The backend should already allow CORS. If you still see errors:

1. Check backend is running on port 8002
2. Clear browser cache (Ctrl+Shift+Delete)
3. Try incognito/private mode

### Issue 7: "Redirect URI mismatch"

**Solution:**
Add exact redirect URIs to Azure AD:

1. Go to Azure Portal → App Registrations → Your App
2. Navigate to: Authentication
3. Add redirect URIs:
   - `http://localhost:8003/index.html`
   - `http://localhost:8002/index.html`
   - `http://127.0.0.1:8003/index.html`
4. Save changes
5. Wait 5 minutes for changes to propagate

## Testing Checklist

Use this checklist to verify everything works:

- [ ] Python virtual environment created and activated
- [ ] All dependencies installed (`pip list` shows packages)
- [ ] `.env` file created with all credentials
- [ ] MongoDB running (or using Atlas/JSON fallback)
- [ ] `test_auth.py` passes all checks
- [ ] Backend server running on port 8002
- [ ] Frontend accessible at `http://localhost:8003/login.html`
- [ ] Can click "Sign in with Microsoft" without errors
- [ ] Microsoft login page loads
- [ ] Can sign in with `@cloudfuze.com` email
- [ ] Redirected back to app after login
- [ ] Can see chat interface after login
- [ ] Can send a message and get response

## Detailed Testing Commands

Run these commands in order:

```bash
# 1. Check Python version (should be 3.8+)
python --version

# 2. Activate virtual environment
# Windows
.\venv\Scripts\Activate.ps1
# Linux/Mac
source venv/bin/activate

# 3. Verify packages installed
pip list | grep fastapi
pip list | grep langchain

# 4. Check environment variables
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Client ID:', os.getenv('MICROSOFT_CLIENT_ID')); print('OpenAI Key:', 'Set' if os.getenv('OPENAI_API_KEY') else 'Missing')"

# 5. Test MongoDB connection (if using)
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000); client.admin.command('ping'); print('MongoDB: Connected'); client.close()"

# 6. Run diagnostic script
python test_auth.py

# 7. Start backend (in one terminal)
python server.py

# 8. Test backend endpoint (in another terminal)
curl http://localhost:8002/health
# Expected: {"status":"healthy","message":"Server is running"}

# 9. Start frontend server
python -m http.server 8003

# 10. Open browser
# Navigate to: http://localhost:8003/login.html
```

## Browser Console Testing

Open browser console (F12) and run these tests:

```javascript
// Test 1: Check API base URL
function getApiBase() {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://127.0.0.1:8002';
  }
  return window.location.origin;
}
console.log('API Base:', getApiBase());

// Test 2: Test backend connectivity
fetch('http://127.0.0.1:8002/health')
  .then(r => r.json())
  .then(data => console.log('✅ Backend:', data))
  .catch(err => console.error('❌ Backend error:', err));

// Test 3: Check OAuth configuration
console.log('Client ID:', '63bd4522-368b-4bd7-a84d-9c7f205cd2a6');
console.log('Tenant:', 'cloudfuze.com');
console.log('Redirect URI:', window.location.origin + '/index.html');

// Test 4: Check storage
console.log('LocalStorage works:', typeof localStorage !== 'undefined');
console.log('SessionStorage works:', typeof sessionStorage !== 'undefined');

// Test 5: Check code verifier (after clicking login)
console.log('Code Verifier:', sessionStorage.getItem('code_verifier') || localStorage.getItem('code_verifier'));
```

## Success Indicators

When everything works correctly, you should see:

### Terminal (Backend)
```
INFO:     Started server process [12345]
✅ MongoDB memory storage initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002
INFO:     127.0.0.1:54321 - "POST /auth/microsoft/callback HTTP/1.1" 200 OK
```

### Browser Console
```
Login page initialized
Current hostname: localhost
API Base URL: http://127.0.0.1:8002
OAuth code received, processing...
✅ Backend: {status: "healthy", message: "Server is running"}
```

### Browser UI
- Login page displays CloudFuze logo
- "Sign in with Microsoft" button is clickable
- Microsoft login page loads
- After login, redirected to chat interface
- User avatar shows in top-right corner
- Can send messages and get responses

## Next Steps

After successful local testing:

1. **Test Chat Functionality:**
   - Send a test message: "What is Slack to Teams migration?"
   - Verify you get a response with CloudFuze information

2. **Test Session Persistence:**
   - Refresh the page
   - You should still be logged in
   - Chat history should be preserved

3. **Test Logout:**
   - Click user avatar → Logout
   - Should redirect to login page
   - Local storage should be cleared

4. **Prepare for Deployment:**
   - Review DEPLOYMENT-GUIDE.md
   - Update production URLs in config
   - Set up production environment variables

## Getting Help

If you're still having issues:

1. **Check logs:**
   - Backend: Terminal output where `server.py` runs
   - Frontend: Browser console (F12)

2. **Run diagnostic:**
   ```bash
   python test_auth.py
   ```

3. **Share error details:**
   - Screenshot of error
   - Browser console logs
   - Backend terminal output
   - Result of `python test_auth.py`

4. **Review documentation:**
   - MICROSOFT-LOGIN-TROUBLESHOOTING.md (detailed troubleshooting)
   - README.md (general project information)
   - DEPLOYMENT-GUIDE.md (deployment instructions)





