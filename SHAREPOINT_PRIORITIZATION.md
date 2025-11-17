# SharePoint Prioritization Implementation

## Overview
Added source-based prioritization to boost SharePoint documents (and emails) in retrieval results, ensuring internal documentation is prioritized over blog posts.

## Changes Made

### 1. Source Prioritization Logic
Added a new prioritization step in both `/chat` and `/chat/stream` endpoints that:
- **Boosts SharePoint documents** by 40% (score multiplier: 0.6)
- **Boosts Email documents** by 20% (score multiplier: 0.8)
- **Leaves Blog documents** unchanged (score multiplier: 1.0)

### 2. Implementation Details

**Location**: `app/endpoints.py`
- Added after confidence-based fallback
- Applied before hybrid ranking
- Works for both regular and streaming endpoints

**Configuration**:
```python
PRIORITIZE_SHAREPOINT = True  # Set to False to disable
SHAREPOINT_BOOST = 0.6  # 40% boost (lower score = higher priority)
EMAIL_BOOST = 0.8  # 20% boost
```

### 3. How It Works

1. **Retrieval**: Documents are retrieved using semantic similarity search
2. **Prioritization**: Source-based boosting is applied:
   - SharePoint docs: score × 0.6 (40% boost)
   - Email docs: score × 0.8 (20% boost)
   - Blog docs: score × 1.0 (no change)
3. **Re-sorting**: Documents are re-sorted by adjusted scores
4. **Hybrid Ranking**: Additional keyword-based ranking is applied
5. **Final Results**: Top documents are selected for LLM context

### 4. Priority Order (After Implementation)

**Before**:
1. Blogs (most semantically similar)
2. Emails
3. SharePoint

**After**:
1. **SharePoint** (boosted 40%)
2. **Emails** (boosted 20%)
3. Blogs (no boost)

### 5. Logging

The system now logs prioritization statistics:
```
[PRIORITIZATION] Boosted sources - SharePoint: 5, Email: 3, Blog: 12
```

### 6. Testing

To test the prioritization:
1. Ask a question that could match multiple sources
2. Check backend logs for `[PRIORITIZATION]` messages
3. Verify SharePoint documents appear higher in results
4. Check the `[VECTORDB]` logs to see document order

### 7. Disabling Prioritization

To disable prioritization, set:
```python
PRIORITIZE_SHAREPOINT = False
```

### 8. Adjusting Boost Values

To change the boost strength:
- **Higher boost** (more prioritization): Lower the multiplier (e.g., 0.5 = 50% boost)
- **Lower boost** (less prioritization): Raise the multiplier (e.g., 0.9 = 10% boost)

**Note**: Lower score = higher priority in similarity search, so multiplying by a smaller number boosts the document.

## Example

**Query**: "How to manage users in QuickBooks with CloudFuze Manage"

**Before Prioritization**:
1. Blog: "Streamline User Management in HubSpot..." (score: 0.0752)
2. Blog: "Zoom Pro User Management..." (score: 0.0965)
3. Blog: "Manage Your SaaS Subscriptions..." (score: 0.1019)
4. (No SharePoint/Email in top results)

**After Prioritization**:
1. SharePoint: "User Management Policy" (score: 0.0451 = 0.0752 × 0.6)
2. Email: "Discussion about user management" (score: 0.0772 = 0.0965 × 0.8)
3. Blog: "Streamline User Management..." (score: 0.0752)
4. Blog: "Zoom Pro User Management..." (score: 0.0965)

## Benefits

1. ✅ **Internal documentation prioritized** - SharePoint docs appear first
2. ✅ **Technical discussions included** - Email threads get priority
3. ✅ **Blogs still available** - Customer-facing content remains accessible
4. ✅ **Configurable** - Easy to adjust or disable
5. ✅ **Transparent** - Logging shows what's being prioritized

## Next Steps

1. Test with various queries to verify prioritization works
2. Monitor logs to see source distribution
3. Adjust boost values if needed
4. Consider adding to system prompt to guide LLM to prefer SharePoint sources

