# Microsoft Login Troubleshooting Guide

## Common Issues and Solutions

### 1. **Missing or Incorrect Environment Variables**

**Problem:** The backend requires Microsoft OAuth credentials that might not be set.

**Solution:**
Create a `.env` file in the project root with:

```env
# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=63bd4522-368b-4bd7-a84d-9c7f205cd2a6
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_TENANT=cloudfuze.com

# OpenAI Configuration
OPENAI_API_KEY=your-openai-key

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_HOST=http://localhost:3100

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories
```

**Check:** Run `python -c "from config import MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_TENANT; print(f'Client ID: {MICROSOFT_CLIENT_ID}\\nTenant: {MICROSOFT_TENANT}')"` to verify the environment variables are loaded.

---

### 2. **Azure AD Application Configuration Issues**

**Problem:** The Azure AD app registration might not be configured correctly.

**Required Azure AD Settings:**

#### A. Redirect URIs
In Azure Portal > App Registrations > Your App > Authentication:

Add these redirect URIs:
- **Development:** `http://localhost:8002/index.html`
- **Development (alt):** `http://127.0.0.1:8002/index.html`
- **Production:** `https://ai.cloudfuze.com/index.html`
- **Production (alt):** `https://newcf3.cloudfuze.com/index.html`

Platform type: **Single-page application (SPA)**

#### B. API Permissions
Required permissions:
- `openid` (default)
- `email` (default)
- `profile` (default)
- `User.Read` (Microsoft Graph)

**Grant admin consent** for these permissions.

#### C. Authentication Settings
- ✅ Enable **Access tokens** (used for implicit flows)
- ✅ Enable **ID tokens** (used for implicit and hybrid flows)
- ✅ Enable **Allow public client flows** for mobile and desktop applications
- ✅ Set **Supported account types** to:
  - "Accounts in this organizational directory only (CloudFuze only - Single tenant)"

#### D. Certificates & Secrets
- Create a new **Client Secret**
- Copy the **Value** (not the Secret ID) to your `.env` file as `MICROSOFT_CLIENT_SECRET`
- **Important:** The secret expires, so note the expiration date

---

### 3. **Code Verifier Issues (PKCE)**

**Problem:** The code verifier might be lost during the OAuth redirect.

**Root Causes:**
- Browser's session storage cleared
- Redirect happens in a different browser tab/context
- Popup blocker preventing redirect

**Solutions:**

#### A. Check Browser Console
Open DevTools (F12) and check for errors like:
```
Code verifier not found, starting fresh login flow...
```

#### B. Verify Session Storage
In browser console, run:
```javascript
console.log(sessionStorage.getItem('code_verifier'));
```
This should show a value after clicking "Sign in with Microsoft".

#### C. Test with Cookies Instead
If session storage doesn't work, modify `login.html`:

```javascript
// Replace sessionStorage with localStorage (more persistent)
// Line 253: Change from:
sessionStorage.setItem('code_verifier', codeVerifier);
// To:
localStorage.setItem('code_verifier', codeVerifier);

// Line 378: Change from:
const codeVerifier = sessionStorage.getItem('code_verifier');
// To:
const codeVerifier = localStorage.getItem('code_verifier');

// Line 419: Change from:
sessionStorage.removeItem('code_verifier');
// To:
localStorage.removeItem('code_verifier');
```

---

### 4. **Domain Restriction Issues**

**Problem:** Only `@cloudfuze.com` emails are allowed.

**Backend Validation (endpoints.py line 1094-1100):**
```python
if not user_email.endswith("@cloudfuze.com"):
    return {
        "error": "Access denied", 
        "message": "Only CloudFuze company accounts are allowed to access this application."
    }
```

**Solutions:**
- Ensure you're using a CloudFuze company account (`user@cloudfuze.com`)
- For testing, temporarily comment out the domain check (lines 1094-1100 in `endpoints.py`)

---

### 5. **CORS Issues**

**Problem:** Browser blocks requests from frontend to backend.

**Current Setup:**
```python
# server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Solutions:**
- ✅ Current setup should work (allows all origins)
- If still blocked, check browser console for CORS errors
- Verify backend is running on the correct port (8002)

---

### 6. **Backend Not Running or Wrong Port**

**Problem:** Frontend can't reach backend API.

**Solution:**

Check backend is running:
```bash
# Windows
netstat -ano | findstr :8002

# Linux/Mac
lsof -i :8002
```

Start backend:
```bash
python server.py
```

Or:
```bash
uvicorn server:app --host 0.0.0.0 --port 8002 --reload
```

---

### 7. **Network Issues or Firewall**

**Problem:** Microsoft's OAuth endpoint is blocked.

**Test Connection:**
```javascript
// In browser console
fetch('https://login.microsoftonline.com/cloudfuze.com/v2.0/.well-known/openid-configuration')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

If this fails, check:
- Corporate firewall settings
- VPN connection
- Proxy configuration

---

## Debugging Steps

### Step 1: Enable Detailed Logging

Add this to `login.html` after line 358:

```javascript
function handleOAuthCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const error = urlParams.get('error');
  const errorDescription = urlParams.get('error_description');

  console.log('=== OAuth Callback Debug ===');
  console.log('Code:', code ? 'Present (length: ' + code.length + ')' : 'Missing');
  console.log('Error:', error);
  console.log('Error Description:', errorDescription);
  console.log('Code Verifier:', sessionStorage.getItem('code_verifier') ? 'Present' : 'Missing');
  console.log('Full URL:', window.location.href);
  console.log('========================');

  if (error) {
    console.error('OAuth error:', error, errorDescription);
    showError('Microsoft login failed: ' + error + (errorDescription ? ' - ' + errorDescription : ''));
    return;
  }

  if (code) {
    console.log('OAuth code received, processing...');
    exchangeCodeForToken(code);
  }
}
```

### Step 2: Test Backend Endpoint

Run this in browser console:

```javascript
// Test backend connectivity
fetch('http://localhost:8002/test')
  .then(r => r.json())
  .then(data => console.log('Backend test:', data))
  .catch(err => console.error('Backend error:', err));

// Test OAuth endpoint
fetch('http://localhost:8002/auth/microsoft/callback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    code: 'test',
    redirect_uri: window.location.origin + '/index.html',
    code_verifier: 'test'
  })
})
  .then(r => r.text())
  .then(data => console.log('OAuth test response:', data))
  .catch(err => console.error('OAuth test error:', err));
```

### Step 3: Check Backend Logs

When you try to login, check the terminal where `server.py` is running for error messages like:

```
Failed to exchange code for token
Failed to get user information
Access denied
```

### Step 4: Verify Azure AD Token Endpoint

Test the Microsoft token endpoint directly:

```bash
curl -X POST https://login.microsoftonline.com/cloudfuze.com/oauth2/v2.0/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=63bd4522-368b-4bd7-a84d-9c7f205cd2a6&client_secret=YOUR_SECRET&grant_type=client_credentials&scope=https://graph.microsoft.com/.default"
```

---

## Quick Diagnostic Script

Create `test_auth.py`:

```python
import os
from dotenv import load_dotenv
import httpx
import asyncio

load_dotenv()

async def test_microsoft_config():
    """Test Microsoft OAuth configuration."""
    print("=" * 60)
    print("Microsoft OAuth Configuration Test")
    print("=" * 60)
    
    # Check environment variables
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    tenant = os.getenv("MICROSOFT_TENANT")
    
    print(f"\n1. Environment Variables:")
    print(f"   Client ID: {'✅ Set' if client_id else '❌ Missing'}")
    print(f"   Client Secret: {'✅ Set' if client_secret else '❌ Missing'}")
    print(f"   Tenant: {tenant or '❌ Missing'}")
    
    if not all([client_id, client_secret, tenant]):
        print("\n❌ Missing required environment variables!")
        return
    
    # Test Azure AD endpoint
    print(f"\n2. Testing Azure AD Endpoint:")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration"
            )
            if response.status_code == 200:
                print(f"   ✅ Azure AD endpoint reachable")
            else:
                print(f"   ❌ Azure AD endpoint returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Cannot reach Azure AD: {e}")
    
    # Test backend connectivity
    print(f"\n3. Testing Backend:")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8002/health")
            if response.status_code == 200:
                print(f"   ✅ Backend is running")
            else:
                print(f"   ⚠️ Backend returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend not reachable: {e}")
        print(f"   💡 Start backend with: python server.py")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_microsoft_config())
```

Run: `python test_auth.py`

---

## Common Error Messages and Solutions

### Error: "Code verifier not found"
**Solution:** Use localStorage instead of sessionStorage (see section 3C)

### Error: "Failed to exchange code for token"
**Solutions:**
1. Check client secret is correct in `.env`
2. Verify code hasn't expired (codes expire in 10 minutes)
3. Check redirect_uri matches Azure AD configuration exactly

### Error: "Access denied - Only CloudFuze company accounts are allowed"
**Solution:** Use a `@cloudfuze.com` email address or temporarily disable domain check

### Error: "AADSTS50011: The reply URL specified in the request does not match"
**Solution:** Add the exact redirect URI to Azure AD app registration

### Error: "AADSTS700016: Application with identifier was not found"
**Solution:** 
1. Verify `MICROSOFT_CLIENT_ID` in `.env` matches Azure AD app
2. Ensure app registration exists in the correct tenant

### Error: "AADSTS7000218: The request body must contain the following parameter: 'client_assertion' or 'client_secret'"
**Solution:** Check `MICROSOFT_CLIENT_SECRET` is set correctly in `.env`

---

## Checklist

- [ ] `.env` file created with all required variables
- [ ] Microsoft Client Secret is valid and not expired
- [ ] Azure AD redirect URIs include your frontend URL
- [ ] API permissions granted (User.Read, openid, email, profile)
- [ ] Admin consent granted for API permissions
- [ ] Backend server is running on port 8002
- [ ] Browser console shows no CORS errors
- [ ] Using a `@cloudfuze.com` email for testing
- [ ] sessionStorage (or localStorage) is working in browser
- [ ] No firewall/proxy blocking Microsoft login endpoints

---

## Need More Help?

If the issue persists:

1. **Capture Full Error Log:**
   - Open browser DevTools (F12)
   - Go to Network tab
   - Try to login
   - Right-click on failed request → Copy → Copy as cURL
   - Share the error details

2. **Check Backend Logs:**
   - Copy the terminal output when login fails
   - Look for specific error codes (AADSTS...)

3. **Verify Azure AD App:**
   - Screenshot the Authentication settings
   - Screenshot the API permissions
   - Verify the Client ID matches





