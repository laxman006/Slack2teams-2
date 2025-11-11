# Outlook Email Integration Guide

## Overview

The Outlook email integration allows your chatbot to access and answer questions based on email conversation threads from Microsoft Outlook. This feature uses the Microsoft Graph API to extract emails from specific folders and integrates them into the knowledge base.

## Features

- ✅ Fetch emails from any Outlook folder (Inbox, custom folders, etc.)
- ✅ Groups emails by conversation thread for better context
- ✅ Preserves email metadata (participants, dates, subject)
- ✅ Supports date filtering (last month, 3 months, 6 months, year)
- ✅ Incremental updates (only processes new/changed emails)
- ✅ Automatic pagination for large mailboxes
- ✅ Uses existing Microsoft authentication (same as SharePoint)

## Prerequisites

### 1. Microsoft Graph API Permissions

Add the following **Application Permission** to your Azure AD app:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations** → Your App
3. Click **API permissions** → **Add a permission**
4. Choose **Microsoft Graph** → **Application permissions**
5. Add: `Mail.Read` (Read mail in all mailboxes)
6. Click **Grant admin consent** (requires admin)

### 2. Verify Existing Setup

Ensure you already have these environment variables set (from SharePoint setup):
```bash
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT=your-tenant-id-or-domain
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable Outlook email source
ENABLE_OUTLOOK_SOURCE=true

# User email address to access (REQUIRED with application permissions)
OUTLOOK_USER_EMAIL=your-email@company.com

# Folder name to extract emails from
OUTLOOK_FOLDER_NAME=Inbox  # or any custom folder name

# Maximum number of emails to fetch
OUTLOOK_MAX_EMAILS=500

# Optional: Date filter
# Options: last_month, last_3_months, last_6_months, last_year, or leave empty for all
OUTLOOK_DATE_FILTER=last_6_months

# Enable vectorstore initialization to load emails
INITIALIZE_VECTORSTORE=true
```

### Configuration Options Explained

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENABLE_OUTLOOK_SOURCE` | Enable/disable Outlook integration | `false` | `true` |
| `OUTLOOK_USER_EMAIL` | Email address to access (required) | `""` | `sales@company.com` |
| `OUTLOOK_FOLDER_NAME` | Folder to extract emails from | `Inbox` | `Sales Conversations` |
| `OUTLOOK_MAX_EMAILS` | Max emails to fetch | `500` | `1000` |
| `OUTLOOK_DATE_FILTER` | Date range filter | `""` (all emails) | `last_6_months` |

## Usage

### Step 1: Configure Environment Variables

Edit your `.env` file:

```bash
# Required settings
ENABLE_OUTLOOK_SOURCE=true
OUTLOOK_USER_EMAIL=your-email@company.com
OUTLOOK_FOLDER_NAME=Sales Conversations

# Optional settings
OUTLOOK_MAX_EMAILS=500
OUTLOOK_DATE_FILTER=last_6_months
INITIALIZE_VECTORSTORE=true
```

### Step 2: Run the Server

```bash
# Development mode
python server.py

# Or with Docker
docker-compose up -d
```

The server will:
1. Authenticate with Microsoft Graph API
2. Find the specified folder
3. Fetch emails from that folder
4. Group emails by conversation thread
5. Add them to the knowledge base

### Step 3: Query Your Emails

Once loaded, you can ask the chatbot questions like:
- "What did we discuss with [client name]?"
- "Summarize the conversation about [topic]"
- "What was decided in the email thread about [project]?"
- "Who are the participants in discussions about [subject]?"

## How It Works

### Email Processing Flow

1. **Authentication**: Uses existing Microsoft credentials (same as SharePoint)
2. **Folder Discovery**: Recursively searches for the specified folder
3. **Email Fetching**: Retrieves emails with pagination support
4. **Thread Grouping**: Groups emails by `conversationId`
5. **Document Creation**: Converts each thread into a single document
6. **Chunking**: Splits large threads for optimal retrieval
7. **Vectorization**: Creates embeddings and adds to knowledge base

### Email Thread Format

Each thread is formatted as:

```
Subject: [Email Subject]
Participants: user1@email.com, user2@email.com
Date Range: 2025-01-01 to 2025-11-06
Number of Emails: 5

================================================================================

--- Email 1 ---
From: John Doe <john@company.com>
Date: 2025-01-01T10:00:00Z

[Email body content]

--- Email 2 ---
From: Jane Smith <jane@company.com>
Date: 2025-01-02T14:30:00Z

[Email body content]

...
```

### Metadata Structure

Each email document includes:

```python
{
  "source_type": "outlook",
  "source": "outlook_email",
  "tag": "email/sales_conversations",  # Based on folder name
  "conversation_id": "AAQkAD...",
  "conversation_topic": "Project X Discussion",
  "participants": "user1@company.com, user2@company.com",  # Comma-separated string
  "date_range": "2025-01-01 to 2025-11-06",
  "email_count": 5,
  "folder_name": "Sales Conversations",
  "first_email_date": "2025-01-01T10:00:00Z",
  "last_email_date": "2025-11-06T16:45:00Z"
}
```

## Advanced Usage

### Using Custom Folders

To extract from a custom folder:

```bash
OUTLOOK_FOLDER_NAME=Sales Conversations
```

The system will:
- Search root folders first
- Recursively search child folders
- Match folder names (case-insensitive)

### Accessing Shared Mailboxes

To access a shared mailbox (e.g., sales team inbox):

```bash
OUTLOOK_USER_EMAIL=sales@company.com
OUTLOOK_FOLDER_NAME=Inbox
```

**Note**: Your Azure AD app needs appropriate permissions to access shared mailboxes.

### Multiple Email Sources

You can access multiple mailboxes by:

1. **Option A**: Change `OUTLOOK_USER_EMAIL` and rebuild
2. **Option B**: (Future) Create multiple processor instances in code

### Incremental Updates

The system automatically detects changes:
- Tracks folder/user configuration
- Only reprocesses when settings change
- Uses metadata comparison for efficiency

To force a full rebuild:
```bash
# Remove metadata file
rm data/vectorstore_metadata.json

# Rebuild
INITIALIZE_VECTORSTORE=true python server.py
```

## Troubleshooting

### Common Issues

#### 1. "OUTLOOK_USER_EMAIL must be set"

**Solution**: Add `OUTLOOK_USER_EMAIL=your@email.com` to `.env`

#### 2. "Folder not found"

**Causes**:
- Folder name typo
- Folder doesn't exist
- Insufficient permissions

**Solution**: 
- Check folder name in Outlook
- Ensure exact spelling (case-insensitive)
- Verify Mail.Read permission granted

#### 3. "Failed to get access token"

**Causes**:
- Invalid client credentials
- Missing permissions
- Admin consent not granted

**Solution**:
- Verify `MICROSOFT_CLIENT_ID` and `MICROSOFT_CLIENT_SECRET`
- Check Azure AD app permissions
- Request admin to grant consent

#### 4. "No emails fetched"

**Causes**:
- Empty folder
- Date filter too restrictive
- Permission issues

**Solution**:
- Check folder has emails
- Remove or adjust `OUTLOOK_DATE_FILTER`
- Verify Mail.Read permission

### Debug Mode

Enable detailed logging:

```python
# In app/outlook_processor.py, the system already prints detailed logs:
# [*] Looking for folder: {folder_name}
# [OK] Found folder '{folder_name}' with ID: {folder_id}
# [*] Fetching batch (current total: {count})...
# [OK] Fetched {count} emails from folder '{folder_name}'
```

### Testing Connection

To test if Outlook integration works:

```bash
# Set environment variables
export ENABLE_OUTLOOK_SOURCE=true
export OUTLOOK_USER_EMAIL=your@email.com
export OUTLOOK_FOLDER_NAME=Inbox
export INITIALIZE_VECTORSTORE=true

# Run server
python server.py

# Check logs for:
# "PROCESSING OUTLOOK EMAIL THREADS"
# "Outlook processing complete: X final chunks"
```

## Security Considerations

1. **Application Permissions**: `Mail.Read` grants access to ALL mailboxes
   - Only grant to trusted applications
   - Regularly audit access logs

2. **Email Privacy**: Emails are stored in the vectorstore
   - Consider excluding sensitive folders
   - Use appropriate date filters

3. **Client Secret Protection**: Never commit `.env` files
   - Use Azure Key Vault for production
   - Rotate secrets regularly

4. **Access Control**: Chatbot can access loaded emails
   - Consider user-level filtering in future versions
   - Document what emails are included

## Architecture

### File Structure

```
app/
├── outlook_processor.py      # Main email processing logic
├── sharepoint_auth.py         # Shared authentication (reused)
├── vectorstore.py             # Vectorstore integration
└── helpers.py                 # Combined source builder

config.py                      # Configuration variables
docker-compose.yml             # Environment variable definitions
```

### Key Components

1. **OutlookProcessor**: Handles email fetching and thread grouping
2. **process_outlook_content()**: Main entry point called by vectorstore
3. **Incremental rebuild**: Only processes changed sources
4. **Metadata tracking**: Detects configuration changes

## Performance

### Typical Processing Times

| Emails | Threads | Processing Time |
|--------|---------|-----------------|
| 100    | ~30     | 10-15 seconds   |
| 500    | ~150    | 30-45 seconds   |
| 1000   | ~300    | 60-90 seconds   |

**Factors affecting performance**:
- Email size (with/without attachments)
- Network speed
- OpenAI API response time
- Number of emails per thread

### Optimization Tips

1. Use date filters to limit scope
2. Start with smaller folders for testing
3. Increase `OUTLOOK_MAX_EMAILS` gradually
4. Monitor OpenAI API token usage

## Future Enhancements

Potential improvements:
- [ ] Label/category-based filtering
- [ ] Attachment extraction
- [ ] Multiple mailbox support
- [ ] Real-time email sync (webhooks)
- [ ] User-level access control
- [ ] Email importance filtering
- [ ] Exclude certain senders/domains

## Support

For issues or questions:
1. Check Azure AD app permissions
2. Review server logs for error messages
3. Verify environment variables
4. Test with a small folder first

## Example Configuration

Complete `.env` example:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Microsoft Authentication
MICROSOFT_CLIENT_ID=abc123...
MICROSOFT_CLIENT_SECRET=xyz789...
MICROSOFT_TENANT=yourdomain.com

# Outlook Email Source
ENABLE_OUTLOOK_SOURCE=true
OUTLOOK_USER_EMAIL=sales@yourdomain.com
OUTLOOK_FOLDER_NAME=Customer Conversations
OUTLOOK_MAX_EMAILS=500
OUTLOOK_DATE_FILTER=last_6_months

# Other Sources
ENABLE_WEB_SOURCE=true
ENABLE_SHAREPOINT_SOURCE=true

# Vectorstore
INITIALIZE_VECTORSTORE=true
```

## Summary

The Outlook email integration provides a powerful way to make your email conversations searchable through your AI chatbot. It seamlessly integrates with your existing Microsoft authentication and follows the same patterns as other data sources in your system.

**Key benefits**:
- Leverages existing conversations as knowledge
- Maintains conversation context through threads
- Supports flexible filtering and configuration
- Integrates seamlessly with existing sources
- Provides incremental updates for efficiency

