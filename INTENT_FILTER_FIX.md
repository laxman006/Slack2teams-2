# Intent Filtering Fix

## Problem
Hard intent-based filtering is excluding relevant documents when:
1. Intent is misclassified (10 categories for 9,000 diverse documents)
2. Documents don't perfectly match intent keywords
3. Tag-based filtering too strict

## Solution: Soft Boosting Instead of Hard Filtering

### Current Code (Lines 602-607):
```python
# HARD EXCLUSION - Bad!
elif intent == "slack_teams_migration":
    if "slack" not in doc_content and "slack" not in doc_title:
        tag_match = False  # ❌ Document excluded completely
    if "teams" not in doc_content and "teams" not in doc_title:
        tag_match = False  # ❌ Document excluded completely
```

### Proposed Fix:
```python
# SOFT BOOSTING - Better!
elif intent == "slack_teams_migration":
    # Boost documents with both keywords, but don't exclude others
    has_slack = "slack" in doc_content or "slack" in doc_title
    has_teams = "teams" in doc_content or "teams" in doc_title
    
    if has_slack and has_teams:
        score = score * 0.5  # Strong boost
    elif has_slack or has_teams:
        score = score * 0.8  # Moderate boost
    # Documents without these keywords still included, just lower priority
```

---

## Specific Changes Needed

### Change 1: Replace Hard Slack/Teams Filtering

**File:** `app/endpoints.py`
**Lines:** 602-607

**Replace:**
```python
elif intent == "slack_teams_migration":
    # Must have both slack and teams keywords
    if "slack" not in doc_content and "slack" not in doc_title:
        tag_match = False
    if "teams" not in doc_content and "teams" not in doc_title:
        tag_match = False
```

**With:**
```python
elif intent == "slack_teams_migration":
    # Boost documents with slack/teams keywords but don't exclude others
    has_slack = "slack" in doc_content or "slack" in doc_title
    has_teams = "teams" in doc_content or "teams" in doc_title
    
    if has_slack and has_teams:
        score = score * 0.5  # Strong boost (both keywords)
    elif has_slack or has_teams:
        score = score * 0.7  # Moderate boost (one keyword)
    # Others still included with original score
```

---

### Change 2: Make Tag Filtering Optional

**File:** `app/endpoints.py`
**Lines:** 540-544

**Replace:**
```python
# Check inclusion tags
include_tags = branch_config.get("include_tags", [])
if include_tags:
    tag_match = any(tag in doc_tag for tag in include_tags)
else:
    tag_match = True
```

**With:**
```python
# Check inclusion tags - BOOST but don't exclude
include_tags = branch_config.get("include_tags", [])
tag_boost = 1.0

if include_tags:
    tag_match = any(tag in doc_tag for tag in include_tags)
    if tag_match:
        tag_boost = 0.7  # Boost matching tags
    else:
        tag_boost = 1.2  # Slight penalty but still include
else:
    tag_match = True

score = score * tag_boost
```

---

### Change 3: Soften General Business Exclusion

**File:** `app/endpoints.py`
**Lines:** 583-599

**Replace:**
```python
if intent == "general_business":
    # Check if document is Slack→Teams specific
    exclude_keywords = branch_config.get("exclude_keywords", [])
    has_excluded = False
    
    # Strong exclusion: if both "slack" and "teams" appear multiple times
    slack_count = doc_content.count("slack")
    teams_count = doc_content.count("teams")
    if slack_count >= 2 and teams_count >= 2:
        has_excluded = True
    
    # Title-based exclusion
    if "slack to teams" in doc_title or "slack-to-teams" in doc_title:
        has_excluded = True
    
    if has_excluded:
        continue  # ❌ Skip this document - TOO HARSH!
```

**With:**
```python
if intent == "general_business":
    # DOWNRANK (not exclude) Slack→Teams specific content
    slack_count = doc_content.count("slack")
    teams_count = doc_content.count("teams")
    
    # Penalize but don't exclude
    if slack_count >= 2 and teams_count >= 2:
        score = score * 1.5  # Penalize heavily but still include
    elif "slack to teams" in doc_title or "slack-to-teams" in doc_title:
        score = score * 1.3  # Penalize moderately
    # Documents still included, just lower priority
```

---

### Change 4: Add Confidence Threshold for Intent

**File:** `app/endpoints.py`
**After line 280 (in classify_intent function)**

**Add:**
```python
# If confidence is low, use "other" intent (minimal filtering)
if confidence < 0.6:
    print(f"[INTENT] Low confidence ({confidence:.2f}) - using 'other' intent for safe retrieval")
    intent = "other"
    confidence = 0.5
```

This prevents aggressive filtering when intent classification is uncertain.

---

## Testing the Fix

After applying changes, test with:

```python
# Test queries that previously failed
queries = [
    ("Are migration logs available for OneDrive?", "Should retrieve audit/logging docs"),
    ("How does JSON Slack to Teams migration work?", "Should get JSON + Slack + Teams docs"),
    ("Does CloudFuze maintain created by metadata?", "Should get metadata docs even if not in intent"),
]

for query, expected in queries:
    # Check that relevant docs aren't excluded
    # Check that results contain expected content
```

---

## Expected Improvements

### Before (with hard filtering):
```
Query: "JSON Slack migration"
Intent: slack_teams_migration
Documents: 150 → filtered to 12 (excluded 138 docs without "teams" keyword!)
Result: Generic answer
```

### After (with soft boosting):
```
Query: "JSON Slack migration"  
Intent: slack_teams_migration
Documents: 150 → scored and ranked (all included, best ranked higher)
Result: Specific answer using "Slack JSON export" doc
```

---

## Why This Matters

With 9,000 documents:
- ✅ Intent helps **prioritize**, not **exclude**
- ✅ Relevant docs always available (just ranked lower if not perfect match)
- ✅ Graceful degradation when intent is wrong
- ✅ Better answers even when classification isn't perfect

---

## Alternative: Remove Intent Filtering Entirely

If you want to be even safer:

```python
# Just use intent for query expansion, not filtering
all_docs = hybrid_retrieve(expanded_query, k=150)

# Apply N-gram boosting and keyword boosting
# But don't filter based on intent

return sorted_docs[:k]  # Let hybrid search + N-grams do the work
```

This relies on:
- ✅ Hybrid search (BM25 + Vector)
- ✅ N-gram detection (your new fix!)
- ✅ Keyword boosting
- ❌ No intent-based exclusion

---

## Recommendation

**Start with Solution 1** (soft boosting) - it gives you the benefits of intent classification (prioritization) without the risks (exclusion).

If results are still not good, move to the alternative (remove intent filtering entirely).

