import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("QUICK TRANSCRIPTION STATUS CHECK")
print("=" * 60)
print()

# Check config
from config import ENABLE_TEAMS_TRANSCRIPTS, TEAMS_TRANSCRIPT_USER_EMAILS

print("✅ Configuration Status:")
print(f"   ENABLE_TEAMS_TRANSCRIPTS = {ENABLE_TEAMS_TRANSCRIPTS}")
print(f"   User emails = {TEAMS_TRANSCRIPT_USER_EMAILS}")
print()

if not ENABLE_TEAMS_TRANSCRIPTS:
    print("❌ ENABLE_TEAMS_TRANSCRIPTS is False!")
    print("   Set ENABLE_TEAMS_TRANSCRIPTS=true in .env")
    sys.exit(1)

# Check for recordings with transcription
from app.teams_transcript_extractor import extract_teams_transcripts

print("🔍 Checking your recordings...")
print()

docs = extract_teams_transcripts(
    user_emails=TEAMS_TRANSCRIPT_USER_EMAILS,
    days_back=30
)

print()
print("=" * 60)
print("RESULTS:")
print("=" * 60)

if docs:
    print(f"✅ SUCCESS! Found {len(docs)} transcript(s)")
    print()
    for i, doc in enumerate(docs, 1):
        print(f"{i}. {doc.metadata.get('recording_name', 'Unknown')}")
        print(f"   Length: {len(doc.page_content)} characters")
        print(f"   Preview: {doc.page_content[:100]}...")
        print()
else:
    print("❌ NO TRANSCRIPTS FOUND")
    print()
    print("Reason: Your recordings don't have transcription enabled.")
    print()
    print("📝 TO FIX THIS:")
    print("1. Open Microsoft Teams")
    print("2. Go to Settings → Privacy → Transcription")
    print("3. Enable 'Allow transcription'")
    print("4. Record a NEW test meeting with transcription ON")
    print("5. Run this script again")
    print()
    print("NOTE: Existing recordings without transcription enabled")
    print("      cannot have their transcripts extracted via API.")

print()







