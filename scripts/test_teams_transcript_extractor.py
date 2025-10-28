import os
import sys
from dotenv import load_dotenv


def main():
    # Ensure project root is on sys.path so we can import the 'app' package
    this_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(this_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # Load environment variables from .env
    load_dotenv()

    # Import here to avoid loading full app config
    from app.teams_transcript_extractor import extract_teams_transcripts

    user_emails_env = os.getenv("TEAMS_TRANSCRIPT_USER_EMAILS")
    user_list = [e.strip() for e in user_emails_env.split(",")] if user_emails_env else None

    days_back = int(os.getenv("TEAMS_TRANSCRIPT_DAYS_BACK", "7"))

    print(f"Running Teams transcript extractor (days_back={days_back}, users={user_list or 'ALL'})...")

    try:
        docs = extract_teams_transcripts(user_emails=user_list, days_back=days_back)
        print(f"TOTAL_TRANSCRIPTS={len(docs)}")
        if docs:
            first = docs[0]
            print(f"FIRST_SUBJECT={first.metadata.get('meeting_subject')}")
            print("FIRST_SNIPPET_START")
            print(first.page_content[:500])
            print("FIRST_SNIPPET_END")
    except Exception as e:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


