#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Outlook Inbox - Direct mailbox access
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  TESTING OUTLOOK INBOX - DIRECT ACCESS")
print("=" * 80)

TEST_EMAIL = "presalesteam@cloudfuze.com"
TEST_FOLDER = "Inbox"

print(f"\nTest: {TEST_EMAIL} / {TEST_FOLDER}")
print("=" * 80)

try:
    from app.outlook_processor import OutlookProcessor
    
    # Override the user email temporarily
    import os
    os.environ['OUTLOOK_USER_EMAIL'] = TEST_EMAIL
    os.environ['OUTLOOK_FOLDER_NAME'] = TEST_FOLDER
    os.environ['OUTLOOK_MAX_EMAILS'] = '10'
    os.environ['OUTLOOK_DATE_FILTER'] = 'last_year'
    
    print("\n[*] Initializing Outlook processor...")
    processor = OutlookProcessor()
    
    print(f"[*] Attempting to fetch emails from '{TEST_FOLDER}'...")
    
    # Try to fetch emails
    emails = processor.get_emails_from_folder(
        folder_name=TEST_FOLDER,
        max_emails=10
    )
    
    if emails:
        print(f"\n[✓] SUCCESS! Retrieved {len(emails)} emails from {TEST_FOLDER}")
        print("\n" + "=" * 80)
        print("  SAMPLE EMAILS")
        print("=" * 80 + "\n")
        
        from datetime import datetime
        
        for i, email in enumerate(emails[:5], 1):
            subject = email.get('subject', 'No Subject')
            from_email = email.get('from', {}).get('emailAddress', {})
            from_name = from_email.get('name', 'Unknown')
            received_date = email.get('receivedDateTime', '')
            
            if received_date:
                try:
                    dt = datetime.fromisoformat(received_date.replace('Z', '+00:00'))
                    received_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            print(f"[{i}] {subject}")
            print(f"    From: {from_name}")
            print(f"    Date: {received_date}")
            print()
        
        print("=" * 80)
        print("✅ TEST PASSED!")
        print("=" * 80)
        print(f"\nConfiguration for full rebuild:")
        print(f"  OUTLOOK_USER_EMAIL={TEST_EMAIL}")
        print(f"  OUTLOOK_FOLDER_NAME={TEST_FOLDER}")
        print(f"  OUTLOOK_DATE_FILTER=last_year")
        print(f"\nTotal emails available: {len(emails)}")
        
    else:
        print(f"\n[!] No emails retrieved")
        print("    This could mean:")
        print("    1. The folder is empty")
        print("    2. No emails from last year")
        print("    3. Permission issue")

except Exception as e:
    print(f"\n[✗] TEST FAILED")
    print(f"Error: {e}")
    
    # Check if it's a 404 error
    if "404" in str(e):
        print("\n❌ User does not exist: presalesteam@cloudfuze.com")
        print("\nPossible reasons:")
        print("  1. Email address has a typo")
        print("  2. This is a shared mailbox (requires different configuration)")
        print("  3. User doesn't exist in your Microsoft 365 tenant")
        print("\nSuggested fixes:")
        print("  • Try: presales@cloudfuze.com")
        print("  • Check Microsoft 365 admin center for correct email")
        print("  • Verify the user has a mailbox assigned")
    
    import traceback
    traceback.print_exc()

