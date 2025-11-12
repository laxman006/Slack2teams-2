# Langfuse Prompt Template for Unified Retrieval

## 📋 Overview

With unified retrieval, we no longer need separate prompts for each intent branch. Instead, we use a single, flexible prompt that adapts to any query type.

---

## 🎯 Recommended Unified Prompt Template

### System Prompt (Langfuse)

Create this prompt in your Langfuse dashboard:

**Prompt Name:** `cloudfuze_unified_system_prompt`
**Version:** `2.0`
**Type:** `text`

```
You are a CloudFuze knowledge assistant. Your role is to provide accurate, helpful answers about CloudFuze's products, services, and migration capabilities.

CloudFuze is a leading cloud-to-cloud data migration and management platform that specializes in:
- Slack to Microsoft Teams migration
- SharePoint to OneDrive migration
- Google Workspace migrations
- Cross-platform data synchronization
- Metadata and permissions preservation
- Compliance and security standards (SOC 2, ISO 27001)

## Response Guidelines

1. **Be Specific and Direct**
   - Answer the user's question directly based on the provided context
   - Include specific features, processes, or technical details when mentioned in context
   - Reference document names, file names, or sources when relevant

2. **Technical Accuracy**
   - For technical queries (JSON, API, metadata), provide precise technical information
   - Explain processes step-by-step when asked "how does X work"
   - Include relevant technical terms and specifications

3. **Migration-Specific Details**
   - When discussing migrations, mention what is preserved (metadata, permissions, timestamps)
   - Explain the migration process clearly
   - Address data security and compliance aspects

4. **Context Handling**
   - The context may include information from multiple sources:
     * Blog posts and articles (general information)
     * SharePoint documents (technical details, policies)
     * Migration guides (step-by-step processes)
     * Technical documentation (APIs, JSON formats)
   - Use information from all relevant sources to provide a comprehensive answer

5. **Honesty and Clarity**
   - If the context doesn't contain enough information, clearly state: "Based on the available information, I don't have specific details about [topic]. However, I recommend [relevant action or alternative]."
   - Don't make up information not present in the context
   - If something is unclear, ask for clarification

6. **Professional Tone**
   - Maintain a professional, helpful, and friendly tone
   - Use clear, concise language
   - Format responses for readability (use bullet points, numbered lists when appropriate)

---

## Context

{{context}}

---

## User Question

{{question}}

---

Please provide your answer:
```

---

## 🔧 Langfuse Configuration

### In Langfuse Dashboard

1. **Navigate to:** Prompts → Create New Prompt

2. **Fill in:**
   - **Name:** `cloudfuze_unified_system_prompt`
   - **Version:** `2.0`
   - **Type:** `Text`
   - **Content:** [Paste the prompt above]
   - **Variables:** 
     * `context` (string)
     * `question` (string)

3. **Save and Publish**

4. **Set as Production:** Mark version 2.0 as production version

---

## 📊 A/B Testing (Optional)

You can create variants to test different prompt styles:

### Variant A: Detailed Technical
For users who prefer technical depth:
```
...include more technical terminology and detailed explanations...
```

### Variant B: Business Focused
For users who prefer business context:
```
...include more business benefits and use case examples...
```

### Variant C: Conversational
For users who prefer casual tone:
```
...use more conversational, friendly language...
```

---

## 🔄 How It Works in Code

### In `app/endpoints.py`

The code already uses Langfuse prompts with fallback:

```python
# Get prompt from Langfuse
langfuse_prompt_template, prompt_metadata = get_system_prompt()

if langfuse_prompt_template:
    # Use Langfuse prompt
    compiled_prompt_text = compile_prompt(
        langfuse_prompt_template,
        context=context,
        question=enhanced_query
    )
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", compiled_prompt_text)
    ])
else:
    # Fallback to config.py SYSTEM_PROMPT
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Context: {context}\n\nQuestion: {question}")
    ])
```

---

## 🧪 Testing Different Prompts

### Quick Test Script

```python
from langfuse import Langfuse
from app.prompt_manager import get_system_prompt, compile_prompt

# Get prompt from Langfuse
langfuse_prompt, metadata = get_system_prompt()

# Test with sample context and question
context = """
[Document 1 - blog]
CloudFuze is a cloud migration platform that helps organizations migrate data between cloud services...

[Document 2 - technical]
JSON Export Format:
{
  "message_id": "123",
  "text": "Hello world",
  "user": "john@example.com"
}
"""

question = "How does JSON work in Slack migration?"

# Compile prompt
compiled = compile_prompt(langfuse_prompt, context, question)
print(compiled)
```

---

## 📈 Monitoring Prompt Performance

### Key Metrics in Langfuse

1. **Response Quality**
   - User feedback (thumbs up/down)
   - Response length distribution
   - Generic answer detection rate

2. **Prompt Usage**
   - Requests per prompt version
   - Success rate (no errors)
   - Average generation time

3. **Context Utilization**
   - Average context length
   - Documents used per query
   - Source diversity

### Query to Monitor Generic Answers

In Langfuse, create a filter:
```
response contains "I don't have specific information"
OR response contains "Based on available information"
```

Target: <5% of responses should be generic

---

## 🎛️ Advanced: Dynamic Prompt Selection

For future enhancement, you can dynamically select prompts based on query characteristics:

```python
def select_prompt_variant(query, detected_ngrams, is_technical):
    """Select optimal prompt variant based on query type."""
    
    if is_technical and len(detected_ngrams) > 3:
        # Technical query - use detailed technical prompt
        return get_system_prompt(prompt_name="cloudfuze_technical_prompt")
    elif any(word in query.lower() for word in ["benefit", "why", "help", "value"]):
        # Business query - use business-focused prompt
        return get_system_prompt(prompt_name="cloudfuze_business_prompt")
    else:
        # Default - unified prompt
        return get_system_prompt(prompt_name="cloudfuze_unified_system_prompt")
```

---

## ✅ Migration Checklist

- [ ] Create unified prompt in Langfuse dashboard
- [ ] Set version 2.0 as production
- [ ] Test prompt with sample queries
- [ ] Monitor response quality in Langfuse
- [ ] Compare A/B variants (optional)
- [ ] Remove old intent-specific prompts
- [ ] Update documentation

---

## 📚 Example Prompt-Response Pairs

### Example 1: Technical Query

**Query:** "How does JSON work in Slack to Teams migration?"

**Context:** [Migration guide + JSON format docs]

**Expected Response:**
```
During Slack to Teams migration, CloudFuze processes data in JSON format through the following steps:

1. **Slack Export**: Slack messages are exported in JSON format, containing:
   - Message ID and text
   - User information
   - Timestamps
   - Attachments and reactions

2. **JSON Parsing**: CloudFuze parses the JSON structure to extract:
   - Channel hierarchy
   - Message threads
   - User mappings
   - File references

3. **Teams Import**: The parsed data is transformed to Teams-compatible format and imported while preserving:
   - Conversation structure
   - Message metadata
   - User permissions

According to the Migration Guide document, this process maintains full message history and metadata integrity.
```

### Example 2: Product Query

**Query:** "What is CloudFuze?"

**Context:** [Blog posts + product overview]

**Expected Response:**
```
CloudFuze is a comprehensive cloud-to-cloud migration and data management platform designed for enterprises.

**Key Capabilities:**
- Migrate data between platforms (Slack to Teams, SharePoint to OneDrive, etc.)
- Preserve metadata, permissions, and timestamps
- Ensure compliance with SOC 2 Type II and ISO 27001 standards
- Provide detailed migration logs and reporting

**Benefits:**
- Zero data loss during migration
- Minimal disruption to business operations
- Automated mapping of users and permissions
- Technical support throughout migration process

CloudFuze is particularly known for its robust Slack to Microsoft Teams migration capabilities, which preserve the entire conversation history and channel structure.
```

---

## 🔗 Related Documentation

- **Unified Retrieval Guide:** `UNIFIED_RETRIEVAL_GUIDE.md`
- **Prompt Manager Source:** `app/prompt_manager.py`
- **Langfuse Integration:** `app/langfuse_integration.py`

---

**Last Updated:** November 12, 2025
**Version:** 2.0 (Unified Retrieval)

