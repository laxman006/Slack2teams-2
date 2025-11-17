#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Show details of test emails fetched from Outlook
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("  FETCHING TEST EMAILS - DETAILS")
print("=" * 80)

try:
    from app.outlook_processor import OutlookProcessor
    from config import OUTLOOK_FOLDER_NAME, OUTLOOK_USER_EMAIL
    from datetime import datetime
    
    print(f"\nUser: {OUTLOOK_USER_EMAIL}")
    print(f"Folder: {OUTLOOK_FOLDER_NAME}")
    print(f"Fetching: 5 most recent emails\n")
    
    processor = OutlookProcessor()
    emails = processor.get_emails_from_folder(
        folder_name=OUTLOOK_FOLDER_NAME,
        max_emails=5
    )
    
    if not emails:
        print("[WARNING] No emails retrieved")
    else:
        print(f"\n{'=' * 80}")
        print(f"  FOUND {len(emails)} EMAILS")
        print(f"{'=' * 80}\n")
        
        for i, email in enumerate(emails, 1):
            subject = email.get('subject', 'No Subject')
            from_email = email.get('from', {}).get('emailAddress', {})
            from_name = from_email.get('name', 'Unknown')
            from_addr = from_email.get('address', 'Unknown')
            
            # To recipients
            to_recipients = email.get('toRecipients', [])
            to_list = []
            for recipient in to_recipients:
                to_addr = recipient.get('emailAddress', {}).get('address', 'Unknown')
                to_list.append(to_addr)
            
            received_date = email.get('receivedDateTime', '')
            if received_date:
                try:
                    dt = datetime.fromisoformat(received_date.replace('Z', '+00:00'))
                    received_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            body_preview = email.get('bodyPreview', '')[:200]
            conversation_id = email.get('conversationId', 'Unknown')
            has_attachments = email.get('hasAttachments', False)
            
            print(f"[{i}] " + "=" * 75)
            print(f"    Subject: {subject}")
            print(f"    From: {from_name} <{from_addr}>")
            print(f"    To: {', '.join(to_list[:3])}{' ...' if len(to_list) > 3 else ''}")
            print(f"    Date: {received_date}")
            print(f"    Conversation ID: {conversation_id[:40]}...")
            print(f"    Has Attachments: {'Yes' if has_attachments else 'No'}")
            print(f"    Preview: {body_preview}...")
            print()
        
        # Group by conversation
        threads = processor.group_emails_by_conversation(emails)
        
        print(f"\n{'=' * 80}")
        print(f"  CONVERSATION THREADS: {len(threads)}")
        print(f"{'=' * 80}\n")
        
        for thread_idx, (conv_id, thread_emails) in enumerate(threads.items(), 1):
            print(f"[Thread {thread_idx}] {len(thread_emails)} email(s)")
            print(f"  Conversation ID: {conv_id[:40]}...")
            print(f"  Subject: {thread_emails[0].get('subject', 'No Subject')}")
            print(f"  Email count in thread: {len(thread_emails)}")
            print()

except Exception as e:
    print(f"[ERROR] Failed to fetch emails: {e}")
    import traceback
    traceback.print_exc()

print("=" * 80)
print("  COMPLETE")
print("=" * 80)

