# How to Test the IDOR Security Fix

## Quick Start - Automated Testing

### 1. Basic Test (No tokens needed)
This tests if endpoints require authentication:

```bash
# Run the automated test script
python test_security_fix.py

# Or for production:
python test_security_fix.py --url https://ai.cloudfuze.com
```

**Expected Result:** All tests should PASS, showing endpoints are protected

---

## Complete IDOR Test (Requires 2 User Accounts)

### 2. Get Your Test Credentials

#### Option A: Using Browser Developer Tools

1. **Log into the app** at https://ai.cloudfuze.com (or localhost)

2. **Open Developer Tools** (F12)

3. **Go to Console tab** and run:
```javascript
// Get your current user info
const user = JSON.parse(localStorage.getItem('user'));
console.log("User ID:", user.id);
console.log("Access Token:", user.access_token);
```

4. **Copy both values** - you'll need them!

5. **Repeat with a second user account** (use a different browser or incognito mode)

#### Option B: Using Network Tab

1. Log in and send a chat message
2. Open Developer Tools → Network tab
3. Look for the `/chat/stream` request
4. Check the **Headers** section:
   - Find `Authorization: Bearer <token>` - that's your token
5. Check the **Payload** section:
   - Find `user_id` - that's your user ID

---

### 3. Run the Complete Test

```bash
python test_security_fix.py \
  --url https://ai.cloudfuze.com \
  --token "YOUR_ACCESS_TOKEN_HERE" \
  --user-id "YOUR_USER_ID_HERE" \
  --other-user-id "ANOTHER_USERS_ID_HERE"
```

**Example:**
```bash
python test_security_fix.py \
  --url https://ai.cloudfuze.com \
  --token "eyJ0eXAiOiJKV1QiLCJhbGc..." \
  --user-id "86d5859b-f6d5-47a9-bfac-81a1d5a18725" \
  --other-user-id "12345678-1234-1234-1234-123456789012"
```

---

## Manual Testing with curl

### Test 1: No Authentication (Should FAIL with 401)
```bash
curl -X GET http://localhost:8000/chat/history/test-user-123
```
**Expected:** `401 Unauthorized` or `403 Forbidden`

---

### Test 2: Access Your Own History (Should SUCCEED)
```bash
curl -X GET http://localhost:8000/chat/history/YOUR_USER_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
**Expected:** `200 OK` with your chat history

---

### Test 3: IDOR Attack - Try to Access Another User's History (Should FAIL with 403)
```bash
curl -X GET http://localhost:8000/chat/history/OTHER_USER_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
**Expected:** `403 Forbidden` with message: "Access denied. You can only access your own resources."

**🚨 If you get `200 OK`, the IDOR vulnerability still exists!**

---

## Manual Testing in Browser

### Test 4: UI Testing

1. **Login as User A** at https://ai.cloudfuze.com

2. **Open Developer Tools** (F12) → Network tab

3. **Send a chat message** and observe:
   - ✅ Request to `/chat/stream` includes `Authorization: Bearer ...`
   - ✅ Response is successful

4. **Try to hack it:**
   - Open Console tab
   - Run this code to try accessing another user's history:
   ```javascript
   fetch('https://ai.cloudfuze.com/chat/history/ANOTHER_USER_ID', {
     method: 'GET',
     headers: {
       'Authorization': `Bearer ${JSON.parse(localStorage.getItem('user')).access_token}`
     }
   })
   .then(r => r.json())
   .then(data => console.log("RESPONSE:", data))
   .catch(e => console.error("ERROR:", e));
   ```

5. **Check the response:**
   - ✅ Should get error: `403 Forbidden`
   - ❌ If you see another user's history → **IDOR still exists!**

---

## Visual Verification

### What Success Looks Like:

#### ✅ Test 1: No Auth
```
❌ Status: 401 Unauthorized
{
  "detail": "Not authenticated"
}
```

#### ✅ Test 2: Access Own Data
```
✅ Status: 200 OK
{
  "user_id": "your-id-here",
  "history": [...]
}
```

#### ✅ Test 3: IDOR Protection (THE KEY TEST!)
```
❌ Status: 403 Forbidden
{
  "detail": "Access denied. You can only access your own resources."
}
```

---

## What Failure Looks Like:

### 🚨 CRITICAL ISSUE - IDOR Still Exists:
```
❌ Test 3 returns: 200 OK
{
  "user_id": "other-users-id",
  "history": [
    {"role": "user", "content": "private message"},
    {"role": "assistant", "content": "private response"}
  ]
}
```
**This means you can see another user's private messages!**

---

## Quick Reference: HTTP Status Codes

| Code | Meaning | Security Status |
|------|---------|-----------------|
| 200 | OK - Success | ✅ Only for own resources |
| 401 | Unauthorized - No/bad token | ✅ Good (auth required) |
| 403 | Forbidden - Valid token, no permission | ✅ Good (IDOR blocked) |
| 404 | Not Found | ⚠️ Neutral |
| 500 | Server Error | ⚠️ Needs investigation |

---

## Troubleshooting

### Issue: "Cannot connect to server"
**Solution:** Make sure the server is running:
```bash
# Check if server is running
curl http://localhost:8000/health

# Start server if needed
python server.py
```

### Issue: "Token expired"
**Solution:** Log in again to get a fresh token. Microsoft tokens expire after ~1 hour.

### Issue: "All tests show 401"
**Solution:** This is actually GOOD! It means authentication is required.

### Issue: Getting 500 errors
**Solution:** Check server logs for errors. The authentication module may have issues.

---

## Reporting Results

When reporting test results, include:

1. **Date/Time** of testing
2. **Environment** (localhost or production)
3. **Test script output** (screenshot or copy/paste)
4. **Any 200 responses** when accessing other user's data (CRITICAL!)
5. **Server logs** if any errors occurred

---

## Success Criteria

✅ **PASS**: All of these must be true:
- Test 1 (No auth): Returns 401 or 403
- Test 2 (Own data): Returns 200 OK
- Test 3 (IDOR): Returns 403 Forbidden
- No other user's data visible in any test

❌ **FAIL**: Any of these occur:
- Can access another user's history (200 OK in Test 3)
- Endpoints work without authentication
- Can delete another user's history

---

## Next Steps After Testing

### If Tests PASS ✅
1. Document test results
2. Deploy to production
3. Monitor logs for authentication failures
4. Consider adding rate limiting

### If Tests FAIL ❌
1. Review code changes in `app/auth.py` and `app/endpoints.py`
2. Check server logs for errors
3. Verify imports are correct
4. Restart the server
5. Re-run tests

---

## Questions?

If you have questions or find issues:
1. Check `SECURITY_FIX_SUMMARY.md` for implementation details
2. Check `SECURITY_TEST_PLAN.md` for comprehensive test cases
3. Review server logs in `server_output.log`

