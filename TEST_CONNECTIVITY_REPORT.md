# Test Connectivity Report

**Test Date:** 2025-11-12T17:41:48.505929

---

## Overall Status

### ✗ TESTS FAILED - Issues Found


---

## Connectivity Results

### ✗ Blogs
**Status:** failed

**Error:** cannot import name 'WEB_URL' from 'config' (C:\Users\LaxmanKadari\Desktop\Slack2teams-2\config.py)


### ✗ SharePoint
**Status:** failed

**Error:** cannot import name 'get_sharepoint_access_token' from 'app.sharepoint_auth' (C:\Users\LaxmanKadari\Desktop\Slack2teams-2\app\sharepoint_auth.py)


### ✗ Outlook
**Status:** failed

**Error:** cannot import name 'get_microsoft_access_token' from 'app.outlook_processor' (C:\Users\LaxmanKadari\Desktop\Slack2teams-2\app\outlook_processor.py)


---

## Vectorstore Test Results

### ✗ Temporary Vectorstore Creation
**Status:** skipped

**Error:** Phase 1 failed - connectivity issues

---

## Query Test Results

### ✗ Query Response Testing
**Status:** skipped

**Error:** Phase 2 failed - no vectorstore

---

## Recommendation

### ✗ ISSUES FOUND - Fix Before Proceeding

Some connectivity tests failed. Please review the errors above and fix:

- **Blogs:** cannot import name 'WEB_URL' from 'config' (C:\Users\LaxmanKadari\Desktop\Slack2teams-2\config.py)
- **SharePoint:** cannot import name 'get_sharepoint_access_token' from 'app.sharepoint_auth' (C:\Users\LaxmanKadari\Desktop\Slack2teams-2\app\sharepoint_auth.py)
- **Outlook:** cannot import name 'get_microsoft_access_token' from 'app.outlook_processor' (C:\Users\LaxmanKadari\Desktop\Slack2teams-2\app\outlook_processor.py)

After fixing issues, re-run this test: `python test_source_connectivity.py`

---


*Report generated: 2025-11-12 17:42:03*
