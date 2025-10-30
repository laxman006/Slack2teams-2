# Teams Meeting Transcripts - Implementation Guide

## ✅ What We've Implemented

A comprehensive Teams transcript extractor that:
- ✅ Searches OneDrive/SharePoint Recordings folders
- ✅ Supports both `.vtt` and `.docx` transcript formats  
- ✅ Falls back to multiple folder locations (`/Recordings`, `/Documents/Recordings`)
- ✅ Checks recording metadata for transcription availability
- ✅ Integrates with your vector database system
- ✅ Scans multiple users' recordings

## ❌ Current Issue: Transcription Not Enabled

### The Problem

Your recordings show:
```json
{
  "isTranscriptionAllowed": False,
  "isAutomaticTranscriptionAllowed": False
}
```

**This means transcription was NOT enabled when these meetings were recorded.**

Even though you can manually download transcripts from the Teams UI (after manually generating them), Microsoft Graph API **does not expose manually-generated transcripts** for recordings where transcription wasn't enabled at recording time.

## ✅ Solution: Enable Transcription Going Forward

### Step 1: Enable Transcription in Teams Settings

1. Open **Microsoft Teams**
2. Go to **Settings** → **Meetings**
3. Under **Recording & transcription**, enable:
   - ☑️ **Transcription**
   - ☑️ **Allow transcription** (if available)

### Step 2: Enable for Each Meeting

When scheduling or starting a meeting:
1. Click **Meeting options**
2. Turn ON **"Allow transcription"**
3. During the meeting, click **"Start transcription"** if not auto-enabled

### Step 3: Record a Test Meeting

1. Record a short test meeting with transcription enabled
2. After the meeting ends, wait a few minutes for processing
3. Run the extractor to verify:

```bash
.\venv\Scripts\python.exe .\scripts\test_teams_transcript_extractor.py
```

## 📊 Expected Results After Enabling

Once transcription is properly enabled, you'll see:

```
[DEBUG] Sample recording metadata:
   - transcription_allowed: True
   - auto_transcription_allowed: True

✅ Found transcript for: Meeting-20251027_120000-Meeting Recording.mp4
   Extracted 1,234 characters
```

## 🔧 Configuration

Add to your `.env` file:

```bash
# Enable Teams transcript extraction
ENABLE_TEAMS_TRANSCRIPTS=true

# How many days back to fetch transcripts (default: 30)
TEAMS_TRANSCRIPT_DAYS_BACK=30

# Specific user emails (comma-separated) or leave empty for all users
TEAMS_TRANSCRIPT_USER_EMAILS=laxman.kadari@cloudfuze.com,Sujana.Manapuram@cloudfuze.com
```

## 🚀 Usage

### Manual Test
```bash
.\venv\Scripts\python.exe .\scripts\test_teams_transcript_extractor.py
```

### Auto-Integration with Vector Store

Once `ENABLE_TEAMS_TRANSCRIPTS=true` in `.env`, transcripts will automatically be:
1. Extracted from OneDrive Recordings folders
2. Parsed (supports VTT and DOCX formats)
3. Added to your vector database
4. Made searchable in your chatbot

### Rebuild Vector Store with Transcripts

```bash
# Set in .env
ENABLE_TEAMS_TRANSCRIPTS=true
INITIALIZE_VECTORSTORE=true

# Run your server or rebuild script
python server.py
```

## 📝 Technical Details

### API Permissions Required

Your app already has these permissions:
- ✅ `Files.Read.All` - Read OneDrive files
- ✅ `Sites.Read.All` - Read SharePoint sites  
- ✅ `OnlineMeetingTranscript.Read.All` - Read meeting transcripts
- ✅ `OnlineMeetings.Read.All` - Read meeting details
- ✅ `OnlineMeetingRecording.Read.All` - Read meeting recordings

### How It Works

1. **Scans OneDrive** for each user's `/Recordings` folder
2. **Checks metadata** to verify transcription was enabled
3. **Extracts transcripts** from:
   - Embedded transcript data (if available)
   - Associated `.vtt` files (WebVTT format)
   - Associated `.docx` files (Word format)
4. **Parses content** to extract plain text
5. **Creates documents** with metadata for vector search
6. **Adds to vector store** for semantic search

### Supported Formats

- **VTT (WebVTT)**: Parsed to remove timestamps and formatting
- **DOCX (Word)**: Extracted using python-docx library
- **TXT**: Direct text extraction

### Metadata Stored

Each transcript document includes:
- `source_type`: "teams_transcript"
- `source`: "microsoft_teams"  
- `content_type`: "meeting_transcript"
- `recording_name`: Original recording filename
- `user_email`: Owner's email
- `web_url`: Link to recording (when available)
- `last_modified`: Timestamp

## ⚠️ Limitations

### Current Limitations

1. **Only works with transcription-enabled recordings**
   - Manually-generated transcripts (post-recording) are NOT accessible via API
   - Must enable transcription BEFORE recording

2. **OnlineMeetings API returns 404**
   - Your meetings aren't accessible via `/users/{id}/onlineMeetings` endpoint
   - This is likely because they're channel meetings or calendar meetings
   - We work around this by scanning OneDrive files directly

3. **No automatic speech-to-text**
   - We don't generate transcripts from audio
   - Only extracts existing transcripts

### Workarounds for Existing Recordings

For recordings that already exist without transcription:

**Option A: Re-record** (Recommended)
- Enable transcription in settings
- Re-record important meetings

**Option B: Manual Transcript Upload** (if you have Word transcripts)
1. Download transcript as `.docx` from Teams UI
2. Place the file in the same folder as the recording with naming: 
   `{Recording Name}-transcript.docx`
3. The extractor will find and process it

**Option C: Third-Party Transcription**
- Extract audio from .mp4 recordings
- Use Azure Speech-to-Text or OpenAI Whisper
- Save as `.vtt` or `.docx` in Recordings folder
- (We can implement this if needed)

## 🎯 Next Steps

1. ✅ **Enable transcription in Teams settings** (most important!)
2. ✅ **Record a test meeting** with transcription enabled
3. ✅ **Run the extractor** to verify it works
4. ✅ **Configure `.env`** with `ENABLE_TEAMS_TRANSCRIPTS=true`
5. ✅ **Rebuild vector store** to add transcripts to knowledge base

## 🆘 Troubleshooting

### No transcripts found

**Check:**
- [ ] Is transcription enabled in Teams settings?
- [ ] Did you start transcription during the meeting?
- [ ] Is `TEAMS_TRANSCRIPT_USER_EMAILS` set correctly in `.env`?
- [ ] Are recordings stored in OneDrive (not just locally)?

### 404 Error on /onlineMeetings

**This is expected!** The API endpoint doesn't work for:
- Channel meetings
- Calendar-scheduled meetings
- Meetings without specific online meeting IDs

Our extractor works around this by scanning OneDrive files directly.

### Transcription not allowed

**Solution:**
- Enable transcription in Teams settings BEFORE recording
- For existing recordings, you'll need to download transcripts manually and place them in the Recordings folder

## 📞 Support

If you encounter issues:
1. Check the logs from `test_teams_transcript_extractor.py`
2. Verify your `.env` configuration
3. Ensure transcription is enabled for new recordings
4. Check Microsoft Teams admin settings for org-wide transcription policies

---

**Status**: ✅ Implementation Complete  
**Waiting On**: Transcription to be enabled for new recordings  
**ETA to Production**: As soon as first transcription-enabled recording is available







