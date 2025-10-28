# SharePoint Content Test Questions

## Questions to Test BEFORE Adding SharePoint (Should FAIL or give generic answers)

These questions test SharePoint-specific content that doesn't exist in your current vectorstore:

### 1. Box Migration Questions
❌ "What are the supported combinations when migrating from Box to OneDrive For Business?"

Expected Current Answer: Generic/unable to answer  
Expected After SharePoint: Specific feature combinations and compatibility details

---

### 2. Dropbox Migration Questions  
❌ "What features are supported when migrating from Dropbox for Business to SharePoint Online?"

Expected Current Answer: Generic/unable to answer  
Expected After SharePoint: Detailed compatibility matrix with specific features like permissions, timestamps, versions, etc.

---

### 3. Slack Migration Questions
❌ "Do we migrate app integration messages from Slack to Teams?"

Expected Current Answer: Generic/unable to answer  
Expected After SharePoint: "No, we don't migrate app integration messages, but they will appear as admin posted messages."

---

### 4. Egnyte Migration Questions
❌ "Can I migrate Egnyte to Google Shared Drive? What features are supported?"

Expected Current Answer: Generic/unable to answer  
Expected After SharePoint: Complete compatibility table with all supported features

---

### 5. White Board Migration
❌ "What white board features can be migrated from Slack to Teams or Google Chat?"

Expected Current Answer: Generic/unable to answer  
Expected After SharePoint: Detailed white board feature migration capabilities

---

### 6. Message Migration
❌ "What are the frequent conflicts faced during Slack to Teams migration?"

Expected Current Answer: Generic/unable to answer  
Expected After SharePoint: "Bad request (Non Retriable): Replied message version conflicts in post, We don't migrate bot messages, Missing body content, Neither body nor adaptive card content contains marker for mention with Id. Resource Modifies (Retryable): Resource has changed - usually an eTag mismatch..."

---

### 7. Teams Migration
❌ "Can I migrate Slack channels into existing Teams? What happens to the messages?"

Expected Current Answer: Generic/unable to answer  
Expected After SharePoint: "Yes, we do migrate Slack channels into existing Teams. But those messages inside a channel will be migrated as admin posted messages."

---

### 8. NFS Migration
❌ "Can I migrate from NFS to cloud storage? What combinations are supported?"

Expected Current Answer: Generic/unable to answer  
Expected After SharePoint: Specific NFS to cloud combinations and features

---

### 9. LinkEX Features
❌ "What LinkEX features are available for data migration?"

Expected Current Answer: Generic/unable to answer  
Expected After SharePoint: Complete LinkEX feature list and combination details

---

### 10. Google Drive to Office 365
❌ "How do I migrate from Google Drive to Office 365? What permissions migrate?"

Expected Current Answer: Generic/unable to answer  
Expected After SharePoint: Detailed Google to Office migration path with permission mapping

---

## Questions That SHOULD Work Now (Control Questions)

These test your existing knowledge base:

✅ "What are the migration capabilities of CloudFuze?"  
   Should work if you have web/blog content

✅ "How does CloudFuze handle data migration?"  
   Should work if you have general documentation

✅ Questions about your existing PDF/Excel/Word docs (if any)

---

## Testing Strategy

### Phase 1: BEFORE Adding SharePoint
1. Ask 2-3 SharePoint questions above
2. Note: Chatbot should say "I don't know" or give generic answers

### Phase 2: Enable SharePoint
1. Set `ENABLE_SHAREPOINT_SOURCE=true` in .env
2. Set `INITIALIZE_VECTORSTORE=true` in .env
3. Run: `python server.py`

### Phase 3: AFTER Adding SharePoint  
1. Ask the same SharePoint questions
2. Chatbot should now provide detailed, specific answers
3. Compare before/after answers

---

## Sample Test Script

```bash
# Before adding SharePoint
python -c "
import sys
sys.path.insert(0, '.')
from app.llm import get_rag_chain
chain = get_rag_chain()

# Test question
question = 'Do we migrate app integration messages from Slack to Teams?'
print('Question:', question)
print('Answer:', chain.invoke({'question': question})['answer'])
"

# After adding SharePoint
# Run the same command and compare results
```

---

## Expected Results

### BEFORE SharePoint:
- Questions: Generic/vague answers or "I don't know"
- Accuracy: Low for migration-specific questions
- Detail: Minimal technical details

### AFTER SharePoint:
- Questions: Specific, detailed answers
- Accuracy: High for migration combinations  
- Detail: Complete feature compatibility matrices, FAQs, step-by-step guides
- Examples: Specific error messages, conflict resolution, feature support

---

## Real-World Test Scenarios

### Scenario 1: Box Migration Inquiry
**Before**: "I don't have specific information about Box to OneDrive migrations..."
**After**: "Yes, Box to OneDrive For Business is supported with the following features: One Time migration, Delta sync, Versions, Folder display, Permissions, Timestamps, and more..."

### Scenario 2: Slack FAQ  
**Before**: Generic migration advice
**After**: "Q: Do we migrate deactivated user DMs? A: We can't migrate deactivated user DMs because deactivated users can't authenticate from Teams. It's a limitation of Teams."

### Scenario 3: Google Drive Combinations
**Before**: Unable to answer
**After**: Complete compatibility table showing all supported destinations, features, and limitations

