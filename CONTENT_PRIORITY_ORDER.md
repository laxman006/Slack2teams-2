# 📊 CONTENT PRIORITY ORDER ANALYSIS

**Current System:** Pure Semantic Similarity (No Manual Priority)  
**Date:** November 13, 2025

---

## 🎯 **CURRENT PRIORITY ORDER**

### **How It Actually Works:**

**The system does NOT have a fixed priority order.** Instead, it uses **semantic similarity scoring** from the vector database (ChromaDB with HNSW indexing).

**Retrieval Flow:**
```
1. User asks question
2. System converts question to embedding vector
3. ChromaDB finds most similar chunks (cosine similarity)
4. Top 25 chunks returned (k=25)
5. Query is rephrased 2 times
6. Each rephrase retrieves 12 more chunks (k=12 x 2 = 24)
7. Total: Up to 49 chunks, deduplicated to ~30
8. Ordered by similarity score (highest first)
9. LLM uses these chunks to generate answer
```

---

## 📈 **SIMILARITY-BASED RANKING**

**What determines priority:**
- ✅ **Semantic similarity** to user's question (0.0 to 1.0)
- ✅ **Embedding quality** (how well the content was vectorized)
- ✅ **Keyword matches** (captured by embeddings)
- ❌ **NOT source type** (blogs, SharePoint, emails treated equally)
- ❌ **NOT tags** (no tag-based prioritization)
- ❌ **NOT recency** (newer content not prioritized)

---

## 📦 **YOUR CONTENT BREAKDOWN**

| Source | Chunks | % of Total |
|--------|--------|------------|
| **Blogs** | 7,176 | 58.8% |
| **Emails** | 3,232 | 26.5% |
| **SharePoint** | 1,794 | 14.7% |
| **TOTAL** | 12,202 | 100% |

**Implicit Priority (by volume):**
1. **Blogs** (largest source = more likely to match)
2. **Emails** (second largest)
3. **SharePoint** (smallest)

---

## 🔍 **HOW SOURCE AFFECTS RESULTS**

### **Current Behavior:**

```
Question: "How to migrate from Slack to Teams?"

Retrieval Process:
1. Semantic search finds top 25 similar chunks
2. Results might be:
   - 15 from Blogs (comprehensive guides)
   - 7 from Emails (technical discussions)
   - 3 from SharePoint (internal docs)
3. All mixed together, ordered by similarity score
4. LLM sees all 25 chunks with source tags
5. LLM decides what to use based on relevance
```

**No source is prioritized over another** - only similarity scores matter.

---

## 📋 **SOURCE TAGS IN CONTEXT**

Each chunk is labeled with its source:

```
[SOURCE: blog]
Content about Slack to Teams migration...

[SOURCE: sharepoint/folder/subfolder]
File: migration-guide.docx
Content about internal process...

[SOURCE: email]
Content from email thread about bugs...
```

**The LLM sees these tags but treats all sources equally.**

---

## ⚠️ **POTENTIAL ISSUES FOR INTERNAL USE**

### **1. Blog Dominance** 🟡

**Issue:** Blogs are 58.8% of all content
- More likely to appear in top results (more chunks to match)
- May overshadow internal docs

**Example:**
```
Question: "What's the process for handling X?"
Results: 18 blog chunks, 5 SharePoint chunks, 2 email chunks
Problem: Blogs are customer-facing; may miss internal-specific info
```

---

### **2. No Recency Bias** 🟡

**Issue:** Old and new content treated equally
- 2-year-old blog post = same priority as yesterday's email
- No time-based relevance

**Example:**
```
Question: "How do we handle API rate limits?"
Results: Might show old blog post from 2023
Problem: May miss recent email discussing 2025 changes
```

---

### **3. No Source-Type Priority** 🟡

**Issue:** All sources treated equally by vector similarity
- Technical internal docs compete with marketing blogs
- Customer guides compete with employee emails

**Example:**
```
Question: "What's our internal policy on X?"
Results: Blog post about customer policy ranks higher
Problem: Similarity score doesn't know "internal" vs "customer"
```

---

## 🎯 **RECOMMENDED PRIORITY ORDERS**

### **For Internal Use (Employee Knowledge Base):**

```
RECOMMENDED PRIORITY:
1. SharePoint Docs     (internal policies, technical docs) ⭐⭐⭐⭐⭐
2. Email Threads       (technical discussions, decisions) ⭐⭐⭐⭐
3. Blogs               (customer-facing, background info) ⭐⭐⭐
```

**Why:**
- SharePoint = authoritative internal source
- Emails = real technical discussions and decisions
- Blogs = helpful but customer-focused

---

### **For Customer Support (External):**

```
RECOMMENDED PRIORITY:
1. Blogs               (comprehensive guides) ⭐⭐⭐⭐⭐
2. SharePoint Docs     (official documentation) ⭐⭐⭐⭐
3. Emails              (not relevant for customers) ⭐
```

---

### **For Mixed Use (Current Setup):**

```
CURRENT IMPLICIT PRIORITY (by volume):
1. Blogs (58.8%)       ⭐⭐⭐⭐
2. Emails (26.5%)      ⭐⭐⭐
3. SharePoint (14.7%)  ⭐⭐
```

**This is NOT intentional** - just a result of having more blog chunks.

---

## 🔧 **HOW TO CHANGE PRIORITY**

### **Option A: Boost Specific Sources (Easy)** ⚡

Add scoring multipliers in retrieval:

```python
# In app/llm.py, after retrieving documents:
for doc in relevant_docs:
    source_type = doc.metadata.get("tag", "")
    
    # Apply priority multipliers
    if "sharepoint" in source_type:
        doc.score *= 1.3  # 30% boost for SharePoint
    elif "email" in source_type:
        doc.score *= 1.2  # 20% boost for emails
    elif "blog" in source_type:
        doc.score *= 1.0  # No boost for blogs

# Re-sort by adjusted scores
relevant_docs.sort(key=lambda x: x.score, reverse=True)
```

**Impact:** SharePoint and emails appear higher in results

---

### **Option B: Separate Collections (Medium)** 🔧

Create different ChromaDB collections:

```
Collection 1: "internal" (SharePoint + Emails)
Collection 2: "public" (Blogs)

Retrieval:
- Search "internal" first (k=20)
- If insufficient results, search "public" (k=10)
```

**Impact:** Internal content always prioritized

---

### **Option C: Query Routing (Advanced)** 🚀

Detect query type and route to appropriate source:

```python
if "internal" or "policy" or "process" in query:
    # Search only SharePoint + Emails
elif "how to" or "guide" or "tutorial" in query:
    # Search Blogs first, then others
```

**Impact:** Smart prioritization based on question type

---

### **Option D: Tag-Based Filtering (Advanced)** 🎯

Allow users to specify source preference:

```
Question: "How to migrate? [source: internal]"
System: Searches only SharePoint + Emails

Question: "How to migrate?"
System: Searches all sources equally
```

**Impact:** User controls priority

---

## 📊 **CURRENT VS IDEAL PRIORITY**

### **Current (Unintentional):**
```
┌─────────────────────────┐
│ Blogs         (58.8%)  │ ← Most content
├─────────────────────────┤
│ Emails        (26.5%)  │
├─────────────────────────┤
│ SharePoint    (14.7%)  │ ← Least content
└─────────────────────────┘
```

### **Ideal for Internal Use:**
```
┌─────────────────────────┐
│ SharePoint    (High)   │ ← Authoritative
├─────────────────────────┤
│ Emails        (Medium) │ ← Technical
├─────────────────────────┤
│ Blogs         (Low)    │ ← Background
└─────────────────────────┘
```

---

## ⚡ **IMMEDIATE RECOMMENDATIONS**

### **For Internal Use (Your Case):**

**Priority Order You Should Have:**
```
1. SharePoint Docs     🥇 (internal policies, tech docs)
2. Email Threads       🥈 (technical discussions)
3. Blog Posts          🥉 (customer guides, background)
```

**How to Achieve This:**

**Quick Fix (Option A):**
```python
# Add to app/llm.py after line 117:
# Boost internal sources
scored_docs = []
for doc in relevant_docs:
    score = 1.0
    tag = doc.metadata.get("tag", "").lower()
    
    if "sharepoint" in tag:
        score = 1.4  # 40% boost
    elif "email" in tag:
        score = 1.2  # 20% boost
    
    scored_docs.append((doc, score))

# Sort by boosted scores
scored_docs.sort(key=lambda x: x[1], reverse=True)
relevant_docs = [doc for doc, score in scored_docs]
```

**Time:** 10 minutes  
**Impact:** SharePoint and emails prioritized

---

## 🎯 **SYSTEM PROMPT CONSIDERATION**

**Current Prompt Says:**
```
"Read through ALL retrieved documents carefully"
```

**Could Be More Explicit:**
```
"Priority for internal employees:
1. First check SharePoint documents (internal policies)
2. Then check email threads (technical discussions)
3. Finally reference blog posts (customer guides)"
```

This would guide the LLM to prefer internal sources even when all are provided.

---

## 📝 **SUMMARY**

### **Current State:**
- ❌ No intentional priority order
- ❌ All sources treated equally
- ❌ Blogs dominate by volume (58.8%)
- ✅ Semantic similarity works well
- ✅ Retrieval is accurate

### **For Internal Use:**
- ⚠️ Should prioritize SharePoint + Emails
- ⚠️ Blogs should be secondary (customer-facing)
- ⚠️ No recency bias (old = new)

### **Recommended Action:**
1. ✅ Add source boosting (Option A) - 10 min
2. ✅ Update system prompt to mention priority - 5 min
3. 🟡 Consider separate collections later (Option B)

---

**Would you like me to implement source-based priority boosting for internal use?**

This would ensure SharePoint docs and emails appear higher in results than blogs for internal employees.

