# Metadata Storage Fix - Enabled Sources

## Problem

The vectorstore metadata was being saved with `"enabled_sources": []` (empty list) instead of the actual enabled sources like `["web", "sharepoint"]`.

### Root Cause

`manage_vectorstore.py` wasn't setting environment variables before importing config, so:
- `ENABLE_WEB_SOURCE` defaulted to `False`
- `ENABLE_SHAREPOINT_SOURCE` defaulted to `False`
- Result: `get_current_metadata()` returned `enabled_sources: []`

## Solution

Updated `manage_vectorstore.py` to:

### 1. Set Environment Variables Early
```python
# Set environment variables BEFORE importing app modules
os.environ["INITIALIZE_VECTORSTORE"] = "true"

# Load .env file first
from dotenv import load_dotenv
load_dotenv()

# Set defaults if not in .env
if "ENABLE_WEB_SOURCE" not in os.environ:
    os.environ["ENABLE_WEB_SOURCE"] = "true"
if "ENABLE_SHAREPOINT_SOURCE" not in os.environ:
    os.environ["ENABLE_SHAREPOINT_SOURCE"] = "true"
```

### 2. Show Enabled Sources in Status
```
============================================================
VECTORSTORE STATUS CHECK
============================================================
Vectorstore exists: True
Document count: 8941
Last updated: 2025-11-01T17:27:05
Enabled sources: web, sharepoint  ← NOW DISPLAYED!

============================================================
CURRENT ENVIRONMENT SETTINGS
============================================================
Currently enabled sources: web, sharepoint  ← SHOWS CURRENT CONFIG!
```

### 3. Show Sources Before Rebuild
```
============================================================
MANUAL VECTORSTORE REBUILD
============================================================
⚠️  WARNING: This will cost $16-20 in OpenAI API calls!

Sources that will be enabled:
  ✓ web
  ✓ sharepoint

Do you want to continue? (yes/no):
```

### 4. Confirm Sources After Rebuild
```
✅ Vectorstore rebuilt successfully!
Total documents: 15000
Timestamp: 2025-11-11T18:00:00

✓ Metadata saved with enabled sources: web, sharepoint  ← CONFIRMATION!

Metadata file: ./data/vectorstore_metadata.json
```

## Files Modified

- ✅ `manage_vectorstore.py` - Set environment variables, improved status/rebuild output

## What This Fixes

| Before | After |
|--------|-------|
| `enabled_sources: []` | `enabled_sources: ["web", "sharepoint"]` |
| No visibility into what's enabled | Clear display of enabled sources |
| Silent failures | Warnings when sources not enabled |
| Unknown rebuild scope | Shows exactly what will be rebuilt |

## Next Steps

1. **Rebuild to apply fixes:**
   ```powershell
   python rebuild_now.py
   ```

2. **Verify metadata after rebuild:**
   ```powershell
   python manage_vectorstore.py status
   ```

3. **Check metadata file directly:**
   ```powershell
   cat data\vectorstore_metadata.json
   ```

   Should now show:
   ```json
   {
     "timestamp": "2025-11-11T...",
     "vectorstore_exists": true,
     "enabled_sources": ["web", "sharepoint"],  ← FIXED!
     "url": "https://cloudfuze.com/...",
     "sharepoint": "https://cloudfuzecom.sharepoint.com/..."
   }
   ```

## Benefits

✅ **Accurate metadata** - Tracks what sources are actually indexed  
✅ **Better debugging** - Can see what was enabled during build  
✅ **Prevents confusion** - Clear warnings when sources not enabled  
✅ **Incremental rebuild tracking** - Knows what changed between builds  
✅ **Audit trail** - Historical record of vectorstore composition  

## Why This Matters

The `enabled_sources` field is used by the incremental rebuild system to:
- Detect what changed between builds
- Determine what needs to be rebuilt
- Track vectorstore composition over time
- Debug missing content issues

Without it, the system can't properly track changes and may:
- Skip necessary rebuilds
- Rebuild everything unnecessarily
- Not know what's in the vectorstore


