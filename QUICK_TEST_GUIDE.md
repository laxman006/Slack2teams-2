# Quick Security Test Guide - How to Verify IDOR is Fixed

## You Need 3 Things to Test:

1. **YOUR access token** (from your logged-in session)
2. **YOUR user ID** (your own ID)
3. **ANOTHER user's ID** (someone else's ID)

---

## 🔍 How to Get These Values

### Step 1: Open the Application
1. Go to **https://ai.cloudfuze.com** (or your local server)
2. **Log in** with your CloudFuze account

### Step 2: Open Browser Developer Tools
Press **F12** or **Right-click → Inspect**

### Step 3: Get Your Token and User ID

**Go to Console tab** and paste this code:

```javascript
const user = JSON.parse(localStorage.getItem('user'));
console.log("=".repeat(70));
console.log("YOUR CREDENTIALS FOR TESTING:");
console.log("=".repeat(70));
console.log("User ID:", user.id);
console.log("Token:", user.access_token);
console.log("=".repeat(70));
```

**Copy the output!** You'll see something like:
```
User ID: 86d5859b-f6d5-47a9-bfac-81a1d5a18725
Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1HTHFqOThW...
```

### Step 4: Get Another User's ID

**Option A - Ask a colleague:**
- Have a colleague log in
- They run the same code and share their **user ID only** (NOT their token!)

**Option B - Use fake ID for basic testing:**
- Use any fake UUID: `12345678-1234-1234-1234-123456789012`
- This will test if the protection exists (should get 403)

---

## 🧪 Now Test the Security Fix

### Test 1: Can you access YOUR OWN history? (Should work ✅)

**In PowerShell:**
```powershell
$Token = "YOUR_TOKEN_HERE"
$YourUserId = "YOUR_USER_ID_HERE"

Invoke-WebRequest -Uri "https://ai.cloudfuze.com/chat/history/$YourUserId" `
  -Headers @{Authorization="Bearer $Token"} `
  | Select-Object StatusCode
```

**Expected Result:** StatusCode : 200 ✅

---

### Test 2: Can you access ANOTHER user's history? (Should FAIL ❌)

**In PowerShell:**
```powershell
$Token = "YOUR_TOKEN_HERE"
$OtherUserId = "ANOTHER_USERS_ID_HERE"

Invoke-WebRequest -Uri "https://ai.cloudfuze.com/chat/history/$OtherUserId" `
  -Headers @{Authorization="Bearer $Token"} `
  | Select-Object StatusCode
```

**Expected Result:** 
```
StatusCode : 403
```
✅ **PASS** - IDOR vulnerability is FIXED!

**If you get:**
```
StatusCode : 200
```
🚨 **FAIL** - IDOR vulnerability STILL EXISTS!

---

## 🎯 Even Easier: Test in Browser Console

Open the browser console (F12) and run:

### Test Your Own Access (Should Work):
```javascript
const user = JSON.parse(localStorage.getItem('user'));
const myId = user.id;
const myToken = user.access_token;

fetch(`https://ai.cloudfuze.com/chat/history/${myId}`, {
  headers: { 'Authorization': `Bearer ${myToken}` }
})
.then(r => {
  console.log("✅ Status:", r.status);
  return r.json();
})
.then(data => console.log("✅ SUCCESS: Can access my own history", data))
.catch(e => console.error("❌ ERROR:", e));
```

**Expected:** Status: 200, see your own chat history ✅

---

### Test IDOR Protection (Should Fail):
```javascript
const user = JSON.parse(localStorage.getItem('user'));
const myToken = user.access_token;
const otherUserId = "PASTE_ANOTHER_USERS_ID_HERE"; // ← Change this!

fetch(`https://ai.cloudfuze.com/chat/history/${otherUserId}`, {
  headers: { 'Authorization': `Bearer ${myToken}` }
})
.then(r => {
  console.log("Status:", r.status);
  if (r.status === 403) {
    console.log("✅ IDOR PROTECTION WORKING! Cannot access other user's data");
  } else if (r.status === 200) {
    console.log("🚨 CRITICAL: IDOR STILL EXISTS! Can access other user's data!");
  }
  return r.json();
})
.then(data => console.log("Response:", data))
.catch(e => console.error("Error:", e));
```

**Expected:** Status: 403 with error message ✅

---

## 📊 What Results Mean

| Status Code | Meaning | Security Status |
|-------------|---------|-----------------|
| **200** (accessing YOUR data) | ✅ Success | GOOD - You can access your own data |
| **403** (accessing OTHER's data) | ❌ Forbidden | **EXCELLENT** - IDOR is FIXED! |
| **200** (accessing OTHER's data) | ✅ Success | 🚨 **CRITICAL BUG** - IDOR exists! |
| **401** | ❌ Unauthorized | Token expired or invalid |

---

## 🎬 Complete Example

Let's say you got these values:

```
Your Token: eyJ0eXAiOiJKV1QiLCJhbGc...
Your User ID: 86d5859b-f6d5-47a9-bfac-81a1d5a18725
Other User ID: 12345678-1234-1234-1234-123456789012
```

**Test in Browser Console:**

```javascript
// TEST 1: Your own data (should work)
fetch('https://ai.cloudfuze.com/chat/history/86d5859b-f6d5-47a9-bfac-81a1d5a18725', {
  headers: { 'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGc...' }
})
.then(r => console.log("My data - Status:", r.status)); // Expect: 200

// TEST 2: Other user's data (should FAIL with 403)
fetch('https://ai.cloudfuze.com/chat/history/12345678-1234-1234-1234-123456789012', {
  headers: { 'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGc...' }
})
.then(r => console.log("Other's data - Status:", r.status)); // Expect: 403
```

---

## ✅ Success Checklist

After testing, you should see:

- [x] Can access my own chat history (200 OK)
- [x] **Cannot** access another user's history (403 Forbidden)
- [x] Error message says "Access denied. You can only access your own resources."
- [x] All API requests in Network tab show Authorization header

---

## 🆘 Troubleshooting

### "Token expired" / 401 errors
**Solution:** Log out and log back in to get a fresh token. Tokens expire after ~1 hour.

### "Cannot find another user's ID"
**Solution:** 
1. Ask a colleague to share their user ID (from localStorage.user.id)
2. OR use a fake UUID just to test the 403 response works
3. The protection should work even with non-existent user IDs

### PowerShell command not working
**Solution:** Use the browser console method instead - it's easier!

---

## 📧 Questions?

If you're unsure about the results:
1. Take a screenshot of the console output
2. Share the status codes you're seeing
3. Check `SECURITY_FIX_SUMMARY.md` for more details

