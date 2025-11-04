# Security Test Plan - IDOR Vulnerability Fix

## Overview
This document provides a comprehensive test plan to verify that the IDOR (Insecure Direct Object Reference) vulnerability in the chat history endpoints has been fixed, and that all authentication mechanisms are working correctly.

## Prerequisites
1. Two CloudFuze Microsoft accounts for testing (User A and User B)
2. Running server instance at https://ai.cloudfuze.com or local development environment
3. Browser developer tools for inspecting network requests
4. Tools like Postman or curl for API testing

## Test Cases

### Test 1: GET /chat/history/{user_id} - IDOR Fix Verification

#### Test 1.1: Access Own Chat History (Should SUCCEED)
**Steps:**
1. Log in with User A's account
2. Note User A's `user_id` from localStorage or network requests
3. Navigate to or fetch: `GET /chat/history/{user_A_id}`
4. Include Authorization header: `Bearer {user_A_access_token}`

**Expected Result:**
- ✅ Status: 200 OK
- ✅ Returns User A's chat history
- ✅ Response contains: `{"user_id": "user_A_id", "history": [...]}`

#### Test 1.2: Access Another User's Chat History WITHOUT Token (Should FAIL)
**Steps:**
1. Using curl or Postman, send request without Authorization header:
```bash
curl -X GET https://ai.cloudfuze.com/chat/history/{user_B_id}
```

**Expected Result:**
- ✅ Status: 401 Unauthorized
- ✅ Error message: "Not authenticated" or similar
- ✅ No chat history data returned

#### Test 1.3: Access Another User's Chat History WITH Valid Token (Should FAIL - IDOR Prevention)
**Steps:**
1. Log in with User A's account
2. Get User A's access token
3. Obtain User B's user_id (from another session or social engineering scenario)
4. Try to access User B's history using User A's token:
```bash
curl -X GET https://ai.cloudfuze.com/chat/history/{user_B_id} \
  -H "Authorization: Bearer {user_A_access_token}"
```

**Expected Result:**
- ✅ Status: 403 Forbidden
- ✅ Error message: "Access denied. You can only access your own resources."
- ✅ No chat history data returned
- ✅ Server logs warning about unauthorized access attempt

#### Test 1.4: Access With Expired Token (Should FAIL)
**Steps:**
1. Use an expired Microsoft OAuth token
2. Try to access any user's chat history

**Expected Result:**
- ✅ Status: 401 Unauthorized
- ✅ Error message: "Invalid or expired access token"

---

### Test 2: DELETE /chat/history/{user_id} - IDOR Fix Verification

#### Test 2.1: Delete Own Chat History (Should SUCCEED)
**Steps:**
1. Log in with User A
2. Delete own chat history:
```bash
curl -X DELETE https://ai.cloudfuze.com/chat/history/{user_A_id} \
  -H "Authorization: Bearer {user_A_access_token}"
```

**Expected Result:**
- ✅ Status: 200 OK
- ✅ Message: "Chat history cleared for user {user_A_id}"
- ✅ User A's history is actually deleted (verify with GET)

#### Test 2.2: Delete Another User's Chat History (Should FAIL)
**Steps:**
1. Log in with User A
2. Try to delete User B's chat history:
```bash
curl -X DELETE https://ai.cloudfuze.com/chat/history/{user_B_id} \
  -H "Authorization: Bearer {user_A_access_token}"
```

**Expected Result:**
- ✅ Status: 403 Forbidden
- ✅ Error message: "Access denied"
- ✅ User B's history remains intact (verify with User B's account)

---

### Test 3: POST /chat - User ID Validation

#### Test 3.1: Send Message With Own User ID (Should SUCCEED)
**Steps:**
1. Log in with User A
2. Send chat message:
```bash
curl -X POST https://ai.cloudfuze.com/chat \
  -H "Authorization: Bearer {user_A_access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is CloudFuze?",
    "user_id": "{user_A_id}"
  }'
```

**Expected Result:**
- ✅ Status: 200 OK
- ✅ Returns answer and trace_id
- ✅ Message saved to User A's history

#### Test 3.2: Send Message With Different User ID (Should FAIL)
**Steps:**
1. Log in with User A
2. Try to send message with User B's ID:
```bash
curl -X POST https://ai.cloudfuze.com/chat \
  -H "Authorization: Bearer {user_A_access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is CloudFuze?",
    "user_id": "{user_B_id}"
  }'
```

**Expected Result:**
- ✅ Status: 403 Forbidden
- ✅ Error: "Cannot access another user's chat session"
- ✅ No message saved to User B's history

#### Test 3.3: Send Message Without User ID (Should SUCCEED - Uses Authenticated User)
**Steps:**
1. Log in with User A
2. Send message without user_id field:
```bash
curl -X POST https://ai.cloudfuze.com/chat \
  -H "Authorization: Bearer {user_A_access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is CloudFuze?"
  }'
```

**Expected Result:**
- ✅ Status: 200 OK
- ✅ Message automatically associated with User A (authenticated user)
- ✅ Returns valid response

---

### Test 4: POST /chat/stream - User ID Validation

#### Test 4.1: Stream Chat With Own User ID (Should SUCCEED)
**Steps:**
1. Log in with User A
2. Open browser developer tools → Network tab
3. Send a chat message through the UI
4. Observe the /chat/stream request

**Expected Result:**
- ✅ Status: 200 OK
- ✅ Authorization header present: `Bearer {token}`
- ✅ Response streams correctly
- ✅ Message saved to User A's history

#### Test 4.2: Stream Chat With Different User ID (Should FAIL)
**Steps:**
1. Intercept /chat/stream request in browser (using browser dev tools or proxy)
2. Modify user_id in request body to another user's ID
3. Send modified request

**Expected Result:**
- ✅ Status: 403 Forbidden
- ✅ Error: "Cannot access another user's chat session"
- ✅ No response stream

---

### Test 5: Admin Endpoints - Authentication Required

#### Test 5.1: GET /dataset/corrected-responses (Should SUCCEED for CloudFuze Users)
**Steps:**
1. Log in with CloudFuze account
2. Request:
```bash
curl -X GET https://ai.cloudfuze.com/dataset/corrected-responses \
  -H "Authorization: Bearer {cloudfuze_access_token}"
```

**Expected Result:**
- ✅ Status: 200 OK
- ✅ Returns corrected responses data

#### Test 5.2: Admin Endpoints Without Auth (Should FAIL)
**Steps:**
1. Request without Authorization header:
```bash
curl -X GET https://ai.cloudfuze.com/dataset/corrected-responses
```

**Expected Result:**
- ✅ Status: 401 Unauthorized

#### Test 5.3: Admin Endpoints With Non-CloudFuze Account (Should FAIL)
**Steps:**
1. Try with personal Microsoft account (non-@cloudfuze.com)

**Expected Result:**
- ✅ Status: 403 Forbidden
- ✅ Error: "Access denied. Only CloudFuze company accounts are allowed."

---

### Test 6: Frontend Integration

#### Test 6.1: Normal Chat Flow
**Steps:**
1. Log in to https://ai.cloudfuze.com
2. Send a message
3. Check browser Network tab

**Expected Result:**
- ✅ All API requests include Authorization header
- ✅ Chat works normally
- ✅ History loads correctly
- ✅ No console errors

#### Test 6.2: New Chat Button
**Steps:**
1. Send some messages
2. Click "New Chat" button
3. Monitor network requests

**Expected Result:**
- ✅ DELETE request includes Authorization header
- ✅ History clears successfully
- ✅ No errors

---

## Security Monitoring

### Logging Verification
Check server logs for:
1. ✅ Successful authentication logs
2. ✅ Failed authentication attempts logged with user IDs
3. ✅ IDOR attempt warnings (403 errors with mismatched user IDs)
4. ✅ No sensitive data (tokens, passwords) in logs

### Rate Limiting (Future Enhancement)
Consider implementing:
- Rate limiting on authentication endpoints
- Brute force protection
- IP-based throttling for repeated 403 errors

---

## Test Results Template

| Test Case | Status | Notes | Tested By | Date |
|-----------|--------|-------|-----------|------|
| 1.1 - Access Own History | ⬜ | | | |
| 1.2 - No Token | ⬜ | | | |
| 1.3 - IDOR Prevention | ⬜ | | | |
| 1.4 - Expired Token | ⬜ | | | |
| 2.1 - Delete Own History | ⬜ | | | |
| 2.2 - Delete Other's History | ⬜ | | | |
| 3.1 - Chat Own ID | ⬜ | | | |
| 3.2 - Chat Other ID | ⬜ | | | |
| 3.3 - Chat No ID | ⬜ | | | |
| 4.1 - Stream Own ID | ⬜ | | | |
| 4.2 - Stream Other ID | ⬜ | | | |
| 5.1 - Admin Access | ⬜ | | | |
| 5.2 - Admin No Auth | ⬜ | | | |
| 5.3 - Admin Non-CloudFuze | ⬜ | | | |
| 6.1 - Frontend Chat | ⬜ | | | |
| 6.2 - Frontend New Chat | ⬜ | | | |

---

## Automated Test Script (Optional)

Create a Python script for automated testing:

```python
import requests
import os

# Configuration
BASE_URL = "https://ai.cloudfuze.com"
USER_A_TOKEN = os.getenv("USER_A_TOKEN")
USER_A_ID = os.getenv("USER_A_ID")
USER_B_ID = os.getenv("USER_B_ID")

def test_idor_protection():
    """Test IDOR vulnerability is fixed"""
    headers = {"Authorization": f"Bearer {USER_A_TOKEN}"}
    
    # Try to access User B's history with User A's token
    response = requests.get(
        f"{BASE_URL}/chat/history/{USER_B_ID}",
        headers=headers
    )
    
    assert response.status_code == 403, "IDOR vulnerability still exists!"
    print("✅ IDOR protection working")

def test_own_history_access():
    """Test user can access own history"""
    headers = {"Authorization": f"Bearer {USER_A_TOKEN}"}
    
    response = requests.get(
        f"{BASE_URL}/chat/history/{USER_A_ID}",
        headers=headers
    )
    
    assert response.status_code == 200, "Cannot access own history!"
    print("✅ Own history access working")

def test_no_auth():
    """Test endpoints require authentication"""
    response = requests.get(f"{BASE_URL}/chat/history/{USER_A_ID}")
    
    assert response.status_code == 401, "Endpoint accessible without auth!"
    print("✅ Authentication required")

if __name__ == "__main__":
    test_no_auth()
    test_own_history_access()
    test_idor_protection()
    print("\n✅ All tests passed!")
```

---

## Remediation Verification Checklist

- ✅ New `app/auth.py` module created with OAuth2 dependencies
- ✅ `get_current_user()` validates Microsoft tokens
- ✅ `verify_user_access()` prevents IDOR by matching user IDs
- ✅ `require_admin()` enforces CloudFuze domain restriction
- ✅ GET /chat/history/{user_id} requires authentication + ownership
- ✅ DELETE /chat/history/{user_id} requires authentication + ownership
- ✅ POST /chat validates user_id matches authenticated user
- ✅ POST /chat/stream validates user_id matches authenticated user
- ✅ Admin endpoints require CloudFuze email
- ✅ Frontend sends Authorization header in all requests
- ✅ No linter errors in Python code
- ✅ Error messages don't leak sensitive information
- ✅ All authentication failures logged for monitoring

---

## Sign-off

**Security Review Completed By:** _________________  
**Date:** _________________  
**Status:** ⬜ PASS ⬜ FAIL ⬜ NEEDS REVISION  
**Notes:** _________________________________

