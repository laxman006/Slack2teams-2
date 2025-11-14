# Feedback Functionality Debug Guide

## ✅ What Was Fixed

1. **Enhanced Error Logging**: Added detailed console logs on both frontend and backend
2. **Better Error Handling**: Improved error messages and recovery
3. **Local Backup**: Feedback is saved locally even if Langfuse fails
4. **Authentication**: Properly validates user tokens

## 🔍 Debugging Steps for Deployment

### 1. Check Browser Console

When clicking like/dislike, check the browser console (F12) for:

```
[FEEDBACK] Sending to: https://ai.cloudfuze.com/feedback
[FEEDBACK] Trace ID: xxx, Rating: thumbs_up
[FEEDBACK] Response status: 200
✅ Feedback submitted successfully: {...}
```

**Common Issues:**
- `401 Unauthorized` → Token expired, user needs to log in again
- `404 Not Found` → API base URL is wrong
- `CORS error` → Nginx/CORS configuration issue
- `Network error` → Server is down or unreachable

### 2. Check Server Logs

Look for these log messages in the backend:

```
[FEEDBACK] Received feedback: trace_id=xxx, rating=thumbs_up, user=user@cloudfuze.com
[FEEDBACK] Langfuse feedback recorded: True
[FEEDBACK] Local feedback history saved
```

**If you don't see these logs:**
- Request is not reaching the backend
- Check nginx configuration
- Check if endpoint is registered

### 3. Verify API Base URL

In `index.html`, check `getApiBase()` function:

```javascript
// Should return correct URL based on hostname
if (hostname === 'ai.cloudfuze.com') {
  return 'https://ai.cloudfuze.com';
}
```

**Test in browser console:**
```javascript
getApiBase()  // Should return your production URL
```

### 4. Check Authentication Token

In browser console:
```javascript
const user = JSON.parse(localStorage.getItem('user'));
console.log('Token exists:', !!user?.access_token);
console.log('Token length:', user?.access_token?.length);
```

**If token is missing/expired:**
- User needs to log in again
- Token might have expired (Microsoft tokens expire after 1 hour)

### 5. Test Endpoint Directly

Use curl or Postman to test:

```bash
curl -X POST https://ai.cloudfuze.com/feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "trace_id": "test_123",
    "rating": "thumbs_up",
    "comment": ""
  }'
```

**Expected response:**
```json
{
  "status": "success",
  "message": "Feedback recorded successfully",
  "trace_id": "test_123",
  "rating": "thumbs_up"
}
```

### 6. Check Nginx Configuration

Verify `/feedback` endpoint is proxied correctly in nginx config:

```nginx
location /feedback {
    proxy_pass http://backend:8002/feedback;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Port $server_port;
}
```

### 7. Check CORS Configuration

In `server.py`, CORS should allow all origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🐛 Common Issues & Solutions

### Issue 1: "401 Unauthorized"
**Cause:** Token expired or invalid
**Solution:** User needs to log in again

### Issue 2: "404 Not Found"
**Cause:** Wrong API base URL or endpoint not registered
**Solution:** 
- Check `getApiBase()` returns correct URL
- Verify router is included in `server.py`: `app.include_router(chat_router)`

### Issue 3: "CORS Error"
**Cause:** CORS not configured properly
**Solution:** 
- Check CORS middleware in `server.py`
- Verify nginx allows CORS headers

### Issue 4: "Network Error"
**Cause:** Server unreachable or nginx misconfigured
**Solution:**
- Check if backend is running
- Verify nginx proxy_pass is correct
- Check firewall rules

### Issue 5: "Feedback not saving"
**Cause:** Langfuse/local storage failing silently
**Solution:**
- Check server logs for errors
- Verify `data/feedback_history.json` is writable
- Check Langfuse credentials

## 📋 Deployment Checklist

- [ ] API base URL is correct in `index.html`
- [ ] Nginx `/feedback` location is configured
- [ ] Backend endpoint is registered (`app.include_router(chat_router)`)
- [ ] CORS middleware is enabled
- [ ] Authentication tokens are valid
- [ ] Server logs show feedback requests
- [ ] Browser console shows no errors
- [ ] Feedback is saved to `data/feedback_history.json`

## 🔧 Quick Test Script

Add this to browser console to test feedback:

```javascript
async function testFeedback() {
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user?.access_token) {
    console.error('Not logged in');
    return;
  }
  
  const apiBase = getApiBase();
  console.log('Testing feedback to:', apiBase);
  
  try {
    const response = await fetch(`${apiBase}/feedback`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${user.access_token}`
      },
      body: JSON.stringify({
        trace_id: 'test_' + Date.now(),
        rating: 'thumbs_up',
        comment: 'Test feedback'
      }),
    });
    
    const data = await response.json();
    console.log('Response:', response.status, data);
  } catch (error) {
    console.error('Error:', error);
  }
}

testFeedback();
```

## 📝 Notes

- Feedback works even if Langfuse fails (saves locally)
- Authentication is required (user must be logged in)
- Trace ID is optional (fallback is generated if missing)
- Feedback buttons are disabled after successful submission

