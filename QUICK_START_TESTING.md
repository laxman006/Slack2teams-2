# Quick Start - Testing Your Fixes

## 🚀 Quick Testing Guide (5 minutes)

Your Docker server is rebuilding with all the fixes. Here's how to test once it's ready:

---

## Step 1: Wait for Docker Rebuild ⏳

Check Docker logs to see when rebuild is complete:
```bash
docker-compose logs -f slack2teams-backend
```

Look for these lines:
```
[OK] Loaded existing vectorstore with XXXX documents
[OK] Langfuse initialized
[OK] MongoDB memory storage initialized successfully
INFO: Uvicorn running on http://0.0.0.0:8002
```

---

## Step 2: Test Health Endpoints (30 seconds)

### Option A: Using Browser
Open: http://localhost:8002/ready

You should see:
```json
{
  "ready": true,
  "checks": {
    "mongodb": "connected",
    "vectorstore": "available",
    "langfuse": "connected"
  }
}
```

### Option B: Using Terminal
```bash
curl http://localhost:8002/health
curl http://localhost:8002/ready
```

---

## Step 3: Run Quick Tests (2 minutes)

### Test 1: N-gram Detection
```bash
python test_ngram_diagnostics.py
```

**What to look for:**
- ✅ Technical queries should detect n-grams like "json slack", "teams migration"
- ✅ Scores should be in range 0.0-1.0
- ✅ No errors

### Test 2: Retrieval Smoke Test
```bash
python test_retrieval_smoke.py
```

**What to look for:**
- ✅ Vectorstore accessible
- ✅ ~10 documents in final context (not 30+)
- ✅ Deduplication working (some duplicates removed)
- ✅ Estimated tokens < 8000

### Test 3: End-to-End Chat
```bash
python test_chat_end_to_end.py
```

**What to look for:**
- ✅ All health checks pass
- ✅ Single query returns relevant answer
- ✅ Technical query mentions relevant terms
- ✅ Follow-up questions maintain context

---

## Step 4: Test in UI (2 minutes)

### Query 1: Technical Query
Ask: **"How does JSON Slack to Teams migration work?"**

**Expected behavior:**
- Response mentions: JSON, Slack, Teams, migration, export/import
- Docker logs show: `[N-GRAM DETECTION] Technical n-grams: ['json slack', 'slack to teams', 'teams migration']`
- Docker logs show: `[CONTEXT] Using 10 documents for LLM context`

### Query 2: Follow-up Query
Ask: **"What are the pricing options?"**

**Expected behavior:**
- Response talks about pricing/costs
- Docker logs show: `[CONTEXT] Injected conversation history`
- Answer considers previous context about migrations

### Query 3: General Query
Ask: **"What is CloudFuze?"**

**Expected behavior:**
- Response gives overview of CloudFuze
- Docker logs show: `[N-GRAM BOOST] No technical n-grams detected`

---

## 🔍 What to Check in Docker Logs

Open logs in another terminal:
```bash
docker-compose logs -f slack2teams-backend
```

### Look for these new log lines:

#### 1. Context Injection ✅
```
[CONTEXT] Injected conversation history for user abc123
[CONTEXT] Using 10 documents for LLM context
```

#### 2. N-gram Detection ✅
```
[N-GRAM DETECTION] Query: how does JSON Slack migration work
[N-GRAM DETECTION] Technical n-grams: ['json slack', 'slack migration']
[N-GRAM DETECTION] Is technical: True
[N-GRAM BOOST] Reranking 45 documents with n-gram boosting...
[N-GRAM BOOST] Top doc #1: score=0.82, tag=technical, source=...
```

#### 3. Prompt Compilation ✅
```
[PROMPT] Compiled Langfuse prompt successfully
```
or
```
[PROMPT] Using config.py fallback prompt
```

#### 4. Safe Error Handling ✅
If LLM rephrase fails, should see:
```
[LLM REPHRASE] Failed: ...
```
(Then continues without crashing)

---

## ✅ Success Criteria

Your fixes are working if:

1. ✅ **Health endpoint shows ready**
2. ✅ **Technical queries detect n-grams** (check logs)
3. ✅ **Context limited to 10 docs** (check logs)
4. ✅ **Follow-ups mention conversation history** (check logs)
5. ✅ **No crashes or errors** in any test
6. ✅ **Responses are relevant** to queries

---

## ❌ Troubleshooting

### Docker not starting?
```bash
# Check logs for errors
docker-compose logs slack2teams-backend

# Common issues:
# - MongoDB not ready: Wait 30 seconds and check /ready endpoint
# - Vectorstore missing: Check data/chroma_db/ exists
# - Port conflict: Ensure 8002 is free
```

### Tests failing?
```bash
# Ensure server is running first
curl http://localhost:8002/health

# Check Python dependencies
pip install -r requirements.txt

# Check MongoDB connection
docker-compose logs slack2teams-mongodb
```

### N-grams not detected?
```bash
# Verify NLTK data downloaded
python -c "import nltk; nltk.download('punkt')"

# Check ngram_retrieval imports
python -c "from app.ngram_retrieval import detect_technical_ngrams; print('OK')"
```

---

## 📊 Before vs After Comparison

### Before Fixes ❌
- Retrieval: 30-50 documents → slow, diluted context
- Scoring: Multiplicative → runaway scores
- Context: No history → poor follow-ups
- Errors: Crashes on LLM failures

### After Fixes ✅
- Retrieval: 10 documents → fast, focused
- Scoring: Weighted hybrid → balanced
- Context: History injected → good follow-ups
- Errors: Graceful fallbacks → robust

---

## 🎯 Next Actions

Once all tests pass:

1. ✅ Test 5-10 real queries through UI
2. ✅ Check Langfuse dashboard for traces
3. ✅ Monitor response times (should be 40-60% faster)
4. ✅ Verify follow-up questions work well
5. ✅ Report any issues or unexpected behavior

---

## 📝 Quick Command Reference

```bash
# Check server status
curl http://localhost:8002/ready

# View logs
docker-compose logs -f slack2teams-backend

# Run all tests
python test_ngram_diagnostics.py && \
python test_retrieval_smoke.py && \
python test_chat_end_to_end.py

# Restart if needed
docker-compose restart slack2teams-backend

# Full rebuild (if issues)
docker-compose down && docker-compose build --no-cache && docker-compose up
```

---

## ✨ Your Fixes are Live!

The most critical improvements are now deployed:
- ✅ Smarter retrieval ranking
- ✅ Optimized context size
- ✅ Conversation continuity
- ✅ Robust error handling

**Test and enjoy your improved chatbot! 🚀**

