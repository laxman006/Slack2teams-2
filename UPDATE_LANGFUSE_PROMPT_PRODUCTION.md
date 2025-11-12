# ✅ Production Fix: Update Langfuse Prompt (5 Minutes)

## 🎯 The Right Solution

Update your **cloudfuze-system-prompt** in Langfuse to properly handle SharePoint documents.

This is the **production-ready fix** that will work for all queries.

---

## 📝 Step-by-Step Instructions

### 1. Open Langfuse

Go to: https://cloud.langfuse.com

### 2. Navigate to Your Prompt

- Click: **Prompts** (left sidebar)
- Find: **cloudfuze-system-prompt**
- Current version: **5** (production)

### 3. Create New Version

- Click: **"New version"** button (top right)
- This creates version **6** (draft)

### 4. Find Section 2

Scroll down and find this section:

```
2. HOW TO USE CONTEXT EFFECTIVELY:
   - Read through ALL retrieved documents carefully
   - Extract and combine relevant details from multiple documents when they clearly relate to the question
   - Provide comprehensive answers using ALL relevant information found
   - If context directly answers the question, respond with confidence
   - If context is related but doesn't fully answer, explain what you know and what's missing
```

### 5. Add New Section RIGHT AFTER Section 2

**Copy and paste this EXACTLY:**

```
3. SHAREPOINT TECHNICAL DOCUMENTS - HIGHEST PRIORITY:
   - SharePoint documents (marked with [SOURCE: sharepoint/...]) are official technical documentation
   - When you see a SharePoint document in the context, it is ALWAYS highly relevant - USE IT!
   - SharePoint documents have HIGHER authority than blog posts for technical details
   - NEVER say "I don't have information" if a relevant SharePoint document is present in the context
   - CRITICAL: If you see a document like "Cloudfuze Slack to Teams Json Export.docx", extract and use its specific content
   - SharePoint docs contain step-by-step guides, technical specifications, and detailed processes - summarize them in your answer
   - When both blog posts AND SharePoint docs are in context, prioritize SharePoint doc content for technical accuracy
```

### 6. Renumber Following Sections

The old section "3. WHEN TO ANSWER..." becomes "4."
The old section "4." becomes "5."
And so on...

### 7. Save and Set as Production

- Click: **"Save"** (bottom right)
- Click: **"Set as Production"**
- Confirm the change

---

## ✅ What This Does

### Before (Current Behavior):
```
Query: "How does JSON work in Slack to Teams migration?"

Context Contains:
- [SOURCE: sharepoint/.../Cloudfuze Slack to Teams Json Export.docx]
- Content: "SLACK JSON Export Migration Process..."

LLM Response:
❌ "I don't have specific information about JSON..."

Problem: LLM sees the document but ignores it
```

### After (With Updated Prompt):
```
Query: "How does JSON work in Slack to Teams migration?"

Context Contains:
- [SOURCE: sharepoint/.../Cloudfuze Slack to Teams Json Export.docx]
- Content: "SLACK JSON Export Migration Process..."

LLM Response:
✅ "In Slack to Teams migration, JSON format is used for exporting Slack data. 
According to the Cloudfuze Slack to Teams Json Export documentation, customers 
can manually export data from Slack which is downloaded as a .zip file containing 
JSON files. These JSON files include: [specific details from the document]..."

Solution: LLM recognizes SharePoint doc as authoritative and uses its content!
```

---

## 🧪 Test After Updating

Once you've updated the Langfuse prompt:

1. **Wait 1-2 minutes** for Langfuse to propagate the change
2. Go to: http://localhost
3. Ask: **"How does JSON work in Slack to Teams migration?"**
4. **Expected:** Detailed answer using the SharePoint JSON Export document

---

## 📊 Why This Is the Right Fix

### ✅ Production-Ready:
- Works for ALL queries, not just JSON ones
- Teaches the LLM to prioritize technical documentation
- No code hacks or temporary workarounds
- Scales as you add more SharePoint documents

### ✅ Universal Benefit:
- Any query that has a relevant SharePoint doc will now get better answers
- Maintains blog post usage for general questions
- Prioritizes authoritative sources (SharePoint) over marketing content (blogs)

### ✅ Maintainable:
- Change is in Langfuse (version controlled)
- Can A/B test different versions
- Easy to update or revert if needed
- No code changes required

---

## 🔄 Alternative: Use the Exact Text

If you prefer, here's the **EXACT FULL SECTION 3** formatted perfectly:

```markdown
3. SHAREPOINT TECHNICAL DOCUMENTS - HIGHEST PRIORITY:
   - SharePoint documents (marked with [SOURCE: sharepoint/...]) are official technical documentation
   - When you see a SharePoint document in the context, it is ALWAYS highly relevant - USE IT!
   - SharePoint documents have HIGHER authority than blog posts for technical details
   - NEVER say "I don't have information" if a relevant SharePoint document is present in the context
   - CRITICAL: If you see a document like "Cloudfuze Slack to Teams Json Export.docx", extract and use its specific content
   - SharePoint docs contain step-by-step guides, technical specifications, and detailed processes - summarize them in your answer
   - When both blog posts AND SharePoint docs are in context, prioritize SharePoint doc content for technical accuracy
```

Just copy-paste this between section 2 and the current section 3.

---

## 💡 Pro Tip: Keep Both Versions

- **Version 5** (current): Keep as backup
- **Version 6** (new): Set as production

If something unexpected happens, you can instantly rollback to version 5 in Langfuse.

---

## ⏱️ Time Required

- **Update Langfuse:** 5 minutes
- **No rebuild needed:** Changes apply immediately
- **Test:** 2 minutes

**Total: 7 minutes to production-ready fix!**

---

## 🎯 Ready to Update?

Go to Langfuse now and make this change. Once it's saved and set as production, test it and let me know the result!

This is the **proper, scalable, production-ready solution** ✅

