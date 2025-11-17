#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test: Get emails from presales@cloudfuze.com involving presalesteam@cloudfuze.com (distribution list)
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  TEST: FILTERED EMAILS")
print("=" * 80)

MAILBOX = "presales@cloudfuze.com"
FILTER_EMAIL = "presalesteam@cloudfuze.com"
FOLDER = "Inbox"
TEST_LIMIT = 20

print(f"\nConfiguration:")
print(f"  Mailbox: {MAILBOX}")
print(f"  Filter: Emails involving {FILTER_EMAIL}")
print(f"  Folder: {FOLDER}")
print(f"  Limit: {TEST_LIMIT} emails")
print("=" * 80)

try:
    from app.sharepoint_auth import sharepoint_auth
    
    print("\n[1/4] Getting access token...")
    access_token = sharepoint_auth.get_access_token()
    print("[✓] Token obtained")
    
    base_url = "https://graph.microsoft.com/v1.0"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    print(f"\n[2/4] Getting '{FOLDER}' folder ID...")
    folders_url = f"{base_url}/users/{MAILBOX}/mailFolders"
    response = requests.get(folders_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    folders = response.json().get("value", [])
    folder_id = None
    
    for folder in folders:
        if folder.get("displayName", "").lower() == FOLDER.lower():
            folder_id = folder.get("id")
            total_items = folder.get("totalItemCount", 0)
            print(f"[✓] Found {FOLDER}: {total_items} total emails")
            break
    
    if not folder_id:
        print(f"[✗] Folder '{FOLDER}' not found")
        sys.exit(1)
    
    print(f"\n[3/4] Fetching emails involving {FILTER_EMAIL}...")
    
    # Build filter for emails involving the distribution list
    # Filter emails where:
    # - From contains presalesteam@cloudfuze.com OR
    # - To contains presalesteam@cloudfuze.com OR
    # - CC contains presalesteam@cloudfuze.com
    
    # Note: Microsoft Graph has limitations on filtering by recipient addresses
    # We'll fetch emails and filter them in code
    
    messages_url = f"{base_url}/users/{MAILBOX}/mailFolders/{folder_id}/messages"
    
    # Calculate last year date
    start_date = datetime.now() - timedelta(days=365)
    date_filter = f"receivedDateTime ge {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    
    params = {
        "$top": 100,  # Fetch more to ensure we get filtered results
        "$select": "subject,from,toRecipients,ccRecipients,receivedDateTime,conversationId,hasAttachments",
        "$orderby": "receivedDateTime desc",
        "$filter": date_filter
    }
    
    response = requests.get(messages_url, headers=headers, params=params, timeout=60)
    response.raise_for_status()
    
    all_emails = response.json().get("value", [])
    
    # Filter emails involving presalesteam@cloudfuze.com
    filtered_emails = []
    
    for email in all_emails:
        # Check From
        from_addr = email.get('from', {}).get('emailAddress', {}).get('address', '').lower()
        
        # Check To recipients
        to_addrs = [r.get('emailAddress', {}).get('address', '').lower() 
                   for r in email.get('toRecipients', [])]
        
        # Check CC recipients
        cc_addrs = [r.get('emailAddress', {}).get('address', '').lower() 
                   for r in email.get('ccRecipients', [])]
        
        # Check if presalesteam@cloudfuze.com is involved
        if (FILTER_EMAIL.lower() in from_addr or 
            FILTER_EMAIL.lower() in to_addrs or 
            FILTER_EMAIL.lower() in cc_addrs):
            filtered_emails.append(email)
        
        # Stop if we have enough
        if len(filtered_emails) >= TEST_LIMIT:
            break
    
    print(f"[✓] Found {len(filtered_emails)} emails involving {FILTER_EMAIL}")
    
    if filtered_emails:
        print(f"\n[4/4] Sample emails:")
        print("=" * 80)
        
        for i, email in enumerate(filtered_emails[:10], 1):
            subject = email.get('subject', 'No Subject')
            from_email = email.get('from', {}).get('emailAddress', {})
            from_name = from_email.get('name', 'Unknown')
            from_addr = from_email.get('address', 'Unknown')
            
            to_list = [r.get('emailAddress', {}).get('address', '') 
                      for r in email.get('toRecipients', [])]
            
            received_date = email.get('receivedDateTime', '')
            if received_date:
                try:
                    dt = datetime.fromisoformat(received_date.replace('Z', '+00:00'))
                    received_date = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            has_attachments = email.get('hasAttachments', False)
            
            print(f"\n[{i}] {subject}")
            print(f"    From: {from_name} <{from_addr}>")
            print(f"    To: {', '.join(to_list[:3])}{' ...' if len(to_list) > 3 else ''}")
            print(f"    Date: {received_date}")
            print(f"    Attachments: {'Yes' if has_attachments else 'No'}")
        
        print("\n" + "=" * 80)
        print("  TEST SUCCESSFUL!")
        print("=" * 80)
        
        print(f"\n✅ Configuration for full rebuild:")
        print(f"   OUTLOOK_USER_EMAIL={MAILBOX}")
        print(f"   OUTLOOK_FOLDER_NAME={FOLDER}")
        print(f"   OUTLOOK_DATE_FILTER=last_year")
        print(f"\n📊 Statistics:")
        print(f"   Total emails scanned: {len(all_emails)}")
        print(f"   Filtered emails (involving {FILTER_EMAIL}): {len(filtered_emails)}")
        print(f"   Filter rate: {len(filtered_emails)/len(all_emails)*100:.1f}%")
        
        print(f"\n⚠️  NOTE: Current implementation will ingest ALL emails from {MAILBOX}")
        print(f"   To filter for only {FILTER_EMAIL}, we need to modify the processor")
        print(f"\n   Would you like me to:")
        print(f"   1. Ingest ALL emails from {MAILBOX} (simpler, more data)")
        print(f"   2. Create custom filter to only ingest emails involving {FILTER_EMAIL}")
        
    else:
        print(f"\n[!] No emails found involving {FILTER_EMAIL} in the last year")
        print(f"    This could mean:")
        print(f"    1. No emails were sent to/from this distribution list")
        print(f"    2. All such emails are older than 1 year")
        print(f"    3. They're in a different folder (Sent Items, Archive, etc.)")

except Exception as e:
    print(f"\n[✗] Test failed: {e}")
    import traceback
    traceback.print_exc()

