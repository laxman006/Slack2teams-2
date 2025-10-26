# 🚀 Quick Test Instructions

Follow these steps **in order** to test the Microsoft login locally.

## ✅ Pre-Test Checklist

Run this command first:
```bash
python test_auth.py
```

**All these should show ✅:**
- MICROSOFT_CLIENT_ID: Set
- MICROSOFT_CLIENT_SECRET: Set
- OPENAI_API_KEY: Set
- Azure AD endpoint reachable

---

## 📝 Step-by-Step Testing

### **Step 1: Start Backend Server**

Open Terminal 1 (PowerShell) and run:

```powershell
# Navigate to project directory
cd C:\Users\LaxmanKadari\Desktop\Slack2teams-2

# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# Start backend
python server.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
✅ MongoDB memory storage initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8002
```

**🔴 Keep this terminal running!**

---

### **Step 2: Open Frontend**

Option A: **Using browser directly** (Recommended)
```
1. Open File Explorer
2. Navigate to: C:\Users\LaxmanKadari\Desktop\Slack2teams-2
3. Right-click on login.html
4. Open with → Your browser (Chrome/Edge)
```

Option B: **Using HTTP server**
```powershell
# In a NEW terminal (Terminal 2)
cd C:\Users\LaxmanKadari\Desktop\Slack2teams-2
python -m http.server 8003

# Then open: http://localhost:8003/login.html
```

---

### **Step 3: Test Login Flow**

1. **Open browser DevTools** (Press F12)
2. Go to **Console** tab
3. Click "**Sign in with Microsoft**" button

**What should happen:**

✅ **Success path:**
```
Login page initialized
OAuth code received, processing...
Authenticating...
[Redirect to chat interface]
```

❌ **Error path:**
```
Code verifier not found
Failed to exchange code for token
Access denied
```

---

### **Step 4: Monitor Backend Logs**

Switch back to Terminal 1 (where server.py is running)

**On successful login:**
```
INFO: POST /auth/microsoft/callback HTTP/1.1 200 OK
```

**On failed login:**
```
INFO: POST /auth/microsoft/callback HTTP/1.1 400 Bad Request
```

---

## 🔍 Common Issues & Quick Fixes

### Issue 1: "Backend not reachable"

**Fix:**
```powershell
# Check if port 8002 is in use
netstat -ano | findstr :8002

# If something is using it, kill the process or use different port
python -m uvicorn server:app --host 0.0.0.0 --port 8005
```

### Issue 2: "Code verifier not found"

**Fix:** Already fixed! We changed to localStorage.

To verify the fix worked:
1. Open browser console (F12)
2. Run: `console.log(localStorage.getItem('code_verifier'))`
3. Should show a value after clicking login

### Issue 3: "Redirect URI mismatch"

**Fix:** Add these URIs to Azure AD:
```
https://ai.cloudfuze.com/index.html
https://newcf3.cloudfuze.com/index.html
http://localhost:8002/index.html
http://localhost:8003/index.html
file:///C:/Users/LaxmanKadari/Desktop/Slack2teams-2/index.html
```

**How to add:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Azure Active Directory → App Registrations → Your App
3. Authentication → Add a platform → Single-page application
4. Add all the URIs above
5. Save

### Issue 4: "Access denied - domain not allowed"

**Cause:** Only `@cloudfuze.com` emails are allowed.

**Temporary fix for testing:**
Edit `app/endpoints.py` line 1095, comment out the domain check:
```python
# Validate that the user has a CloudFuze email domain
# if not user_email.endswith("@cloudfuze.com"):
#     return {
#         "error": "Access denied", 
#         "message": "Only CloudFuze company accounts are allowed."
#     }
```

**Remember to uncomment before production deployment!**

### Issue 5: "Cannot start backend - ModuleNotFoundError"

**Fix:**
```powershell
pip install -r requirements.txt

# Or install missing packages individually:
pip install fastapi uvicorn httpx python-dotenv
pip install langchain langchain-openai langchain-community
pip install motor pymongo chromadb
```

---

## 🧪 Testing Commands

Run these in browser console (F12) to debug:

```javascript
// Test 1: Check storage is working
localStorage.setItem('test', 'works');
console.log('LocalStorage:', localStorage.getItem('test'));
localStorage.removeItem('test');

// Test 2: Check backend connectivity
fetch('http://localhost:8002/health')
  .then(r => r.json())
  .then(data => console.log('✅ Backend:', data))
  .catch(err => console.error('❌ Backend:', err));

// Test 3: Check code verifier after clicking login
console.log('Code Verifier:', localStorage.getItem('code_verifier'));

// Test 4: Check API configuration
console.log('API Base:', window.location.hostname === 'localhost' ? 'http://127.0.0.1:8002' : window.location.origin);
```

---

## 📊 Complete Test Checklist

Run through this checklist:

**Environment Setup:**
- [ ] `.env` file exists with all credentials
- [ ] `python test_auth.py` passes (shows mostly ✅)
- [ ] Virtual environment activated

**Backend:**
- [ ] `python server.py` runs without errors
- [ ] Can access http://localhost:8002/health
- [ ] Shows: `{"status":"healthy"}`

**Frontend:**
- [ ] `login.html` opens in browser
- [ ] CloudFuze logo displays
- [ ] "Sign in with Microsoft" button visible
- [ ] Browser console shows no errors (F12)

**Login Flow:**
- [ ] Click "Sign in with Microsoft"
- [ ] Microsoft login page loads
- [ ] Can enter credentials
- [ ] Redirected back to app
- [ ] See chat interface (index.html)
- [ ] User avatar shows in top-right

**Chat Functionality:**
- [ ] Can type in message box
- [ ] Can send message (Enter or click send)
- [ ] Receive response from bot
- [ ] Can use thumbs up/down buttons
- [ ] Can copy message
- [ ] Can start new chat

---

## 🎯 Quick Verification Commands

Run these to verify everything is working:

```powershell
# 1. Check environment
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ Client ID set' if os.getenv('MICROSOFT_CLIENT_ID') else '❌ Client ID missing')"

# 2. Test backend health
curl http://localhost:8002/health

# 3. Check if port 8002 is listening
netstat -ano | findstr :8002

# 4. Verify Python packages
pip list | findstr fastapi
pip list | findstr langchain
```

---

## 📸 What Success Looks Like

### Terminal Output:
```
INFO:     Started server process [12345]
✅ MongoDB memory storage initialized successfully  
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002
INFO:     127.0.0.1:50000 - "POST /auth/microsoft/callback HTTP/1.1" 200 OK
INFO:     127.0.0.1:50001 - "GET /chat/history/user-id-here HTTP/1.1" 200 OK
INFO:     127.0.0.1:50002 - "POST /chat/stream HTTP/1.1" 200 OK
```

### Browser Console:
```
Login page initialized
Current hostname: localhost
API Base URL: http://127.0.0.1:8002
OAuth code received, processing...
User found in localStorage, verifying token...
Token is valid, redirecting to index.html
```

### Browser UI:
- ✅ Login page with CloudFuze logo
- ✅ Microsoft login works
- ✅ Chat interface loads
- ✅ Can send/receive messages
- ✅ User avatar in top-right corner

---

## 🆘 Still Not Working?

If you're still having issues after following all steps:

1. **Capture full error logs:**
   - Browser console (F12 → Console tab)
   - Backend terminal output
   - Screenshot of error

2. **Re-run diagnostic:**
   ```bash
   python test_auth.py
   ```

3. **Check these files exist:**
   - `.env` (with credentials)
   - `login.html`
   - `index.html`
   - `server.py`
   - `app/endpoints.py`

4. **Verify Azure AD settings:**
   - Client ID matches `.env`
   - Client Secret is valid (not expired)
   - Redirect URIs are correct
   - API permissions granted

5. **Try with different browser:**
   - Chrome (recommended)
   - Edge
   - Firefox
   - Try incognito/private mode

---

## 📚 Additional Resources

- **Detailed Troubleshooting:** `MICROSOFT-LOGIN-TROUBLESHOOTING.md`
- **Local Testing Guide:** `LOCAL-TESTING-GUIDE.md`
- **Diagnostic Script:** `python test_auth.py`
- **Quick Start:** `quick-start.bat` or `quick-start.sh`



