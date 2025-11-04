# CloudFuze Chatbot - Promptfoo Test Suite

Automated testing framework for the CloudFuze chatbot using promptfoo. Tests the complete FastAPI endpoint including RAG pipeline, memory, and middleware.

## Prerequisites

- **Node.js** (v16 or higher) - [Download](https://nodejs.org/)
- **npm** (comes with Node.js)
- **FastAPI server running** on `http://localhost:8002`
- **Promptfoo installed** (automatic via npx)

## Quick Start

### 1. Install Dependencies (First Time Only)

From the project root directory:

```bash
npm install
```

This installs promptfoo as a dev dependency.

### 2. Start the FastAPI Server

In a separate terminal:

```bash
python server.py
```

Verify it's running by visiting: http://localhost:8002/health

### 3. Run Tests

#### Option A: Using Helper Scripts (Recommended)

**Windows:**
```cmd
cd promptfoo
run-tests.bat
```

**Linux/Mac:**
```bash
cd promptfoo
chmod +x run-tests.sh
./run-tests.sh
```

#### Option B: Using npm Scripts

From project root:
```bash
npm test              # Run tests only
npm run test:view     # Run tests and open viewer
npm run view          # Open viewer for previous results
```

#### Option C: Direct promptfoo Commands

From promptfoo directory:
```bash
npx promptfoo eval                    # Run tests
npx promptfoo view                    # View results
npx promptfoo eval -c promptfooconfig.yaml  # Explicit config
```

## Test Suite Overview

### 15 Core Test Cases (4 Categories)

1. **Core Business Questions (3 tests)**
   - What is CloudFuze?
   - What does CloudFuze do?
   - Pricing inquiry

2. **High-Value Migrations (5 tests)**
   - Slack to Teams
   - Gmail to Outlook
   - Teams to Teams
   - Box to SharePoint
   - Google Drive to SharePoint

3. **Certificate/Document Downloads (4 tests)**
   - SOC 2 certificate download
   - Available certificates inquiry
   - Policy documents inquiry
   - Security policies inquiry

4. **Refusal Behavior (3 tests)**
   - Unrelated geography question
   - Cooking question
   - Weather question

## Viewing Results

### Web UI

After running tests, the browser automatically opens at `http://localhost:15500` showing:

- ✅ Pass/fail status for each test
- 📊 Overall success rate
- 💰 Cost per test
- ⏱️ Latency metrics
- 📝 Detailed failure explanations
- 🔍 Full request/response logs

### Exporting Results

```bash
# Export as JSON
npx promptfoo eval --output results.json

# Export as HTML report
npx promptfoo eval --output report.html

# Export as CSV
npx promptfoo eval --output results.csv

# Share online (generates public link)
npx promptfoo share
```

## Adding New Test Cases

Edit `test-cases.yaml` and add your test:

```yaml
- description: "Your test description"
  vars:
    question: "Your test question"
  assert:
    - type: contains
      value: "expected text"
    - type: llm-rubric
      value: "Quality criteria"
      threshold: 0.7
```

### Available Assertion Types

- `contains` - Check if response contains text
- `contains-all` - Check if response contains all items
- `contains-any` - Check if response contains any item
- `not-contains` - Check if response doesn't contain text
- `regex` - Regex pattern matching
- `javascript` - Custom JavaScript validation
- `llm-rubric` - LLM-based quality evaluation
- `similar` - Semantic similarity check
- `latency` - Response time threshold

## Troubleshooting

### Server Not Running

**Error:** `Connection refused` or `ECONNREFUSED`

**Solution:**
```bash
# Start the server in another terminal
python server.py

# Verify it's running
curl http://localhost:8002/health
```

### Streaming Response Issues

**Error:** Response parsing fails or shows raw SSE data

**Solution:** The config includes a custom `responseParser` that handles streaming. If issues persist, check that the API returns responses in the expected format.

### Timeout Errors

**Error:** `Request timeout after 30000ms`

**Solution:** Some RAG queries take time. Increase timeout in `promptfooconfig.yaml`:

```yaml
defaultTest:
  options:
    provider:
      config:
        timeout: 60000  # 60 seconds
```

### npm/npx Not Found

**Solution:** Install Node.js from https://nodejs.org/

### Permission Denied (Linux/Mac)

**Solution:** Make scripts executable:
```bash
chmod +x run-tests.sh
```

### Tests Failing Unexpectedly

**Debug Steps:**

1. **Check server logs** for errors
2. **Test manually** via browser or curl:
   ```bash
   curl -X POST http://localhost:8002/api/chat \
     -H "Content-Type: application/json" \
     -d '{"user_id":"test","message":"What is CloudFuze?"}'
   ```
3. **Run single test** with verbose output:
   ```bash
   npx promptfoo eval --filter "What is CloudFuze" --verbose
   ```
4. **Check vectorstore** - Ensure RAG data is loaded

## Configuration Files

- `promptfooconfig.yaml` - Main configuration (provider, settings)
- `test-cases.yaml` - Test cases and assertions
- `prompts/system-prompt.txt` - Reference system prompt
- `outputs/` - Test results (auto-generated, gitignored)

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run Promptfoo Tests
  run: |
    python server.py &
    sleep 10
    npm test
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
npm test || exit 1
```

## Cost Tracking

Typical costs per test run (15 tests):

- **GPT-4o-mini:** ~$0.20-0.30
- **GPT-4:** ~$1.50-2.00

Costs depend on:
- Response length
- Number of retrieved documents
- Query rephrasing (if enabled)

## Performance Benchmarks

Expected performance (15 tests):

- **Duration:** 45-90 seconds
- **Concurrency:** 3 parallel tests
- **Avg latency:** 2-4 seconds per test
- **Pass rate target:** 85%+

## Next Steps

1. ✅ Run the initial 15 tests
2. 📊 Review results in UI
3. 🔧 Fix any failing tests
4. 📈 Expand to 50+ tests from `test_50_questions.py`
5. 🔄 Integrate into CI/CD pipeline
6. 📅 Schedule daily regression tests

## Support

- **Promptfoo Docs:** https://promptfoo.dev/docs/intro
- **Issues:** Check FastAPI server logs and promptfoo verbose output
- **Questions:** Review this README's troubleshooting section

---

**Happy Testing! 🚀**

