#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Outlook Inbox access with presalesteam@cloudfuze.com
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  TESTING OUTLOOK INBOX ACCESS")
print("=" * 80)

# Test configuration
TEST_EMAIL = "presalesteam@cloudfuze.com"
TEST_FOLDER = "Inbox"
TEST_DATE_FILTER = "last_year"
TEST_MAX_EMAILS = 10

print(f"\nTest Configuration:")
print(f"  Email: {TEST_EMAIL}")
print(f"  Folder: {TEST_FOLDER}")
print(f"  Date Filter: {TEST_DATE_FILTER}")
print(f"  Max Emails: {TEST_MAX_EMAILS}")
print("=" * 80)

try:
    from app.sharepoint_auth import sharepoint_auth
    
    # Get access token
    print("\n[1/4] Getting Microsoft Graph access token...")
    access_token = sharepoint_auth.get_access_token()
    print("[✓] Access token obtained")
    
    # Initialize Outlook processor with test email
    print(f"\n[2/4] Testing access to {TEST_EMAIL}...")
    
    import requests
    base_url = "https://graph.microsoft.com/v1.0"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    # Test 1: Can we access this user?
    print(f"[*] Checking if user exists: {TEST_EMAIL}")
    user_url = f"{base_url}/users/{TEST_EMAIL}"
    
    try:
        response = requests.get(user_url, headers=headers, timeout=30)
        response.raise_for_status()
        user_info = response.json()
        print(f"[✓] User found: {user_info.get('displayName', 'Unknown')}")
        print(f"    Mail: {user_info.get('mail', 'N/A')}")
        print(f"    UPN: {user_info.get('userPrincipalName', 'N/A')}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"[✗] User NOT FOUND: {TEST_EMAIL}")
            print(f"    Error: {e.response.json()}")
            print("\n[!] This email address does not exist in your Microsoft 365 tenant")
            print("    Please verify the correct email address")
            sys.exit(1)
        else:
            raise
    
    # Test 2: Can we access their mailbox?
    print(f"\n[3/4] Looking for '{TEST_FOLDER}' folder...")
    folders_url = f"{base_url}/users/{TEST_EMAIL}/mailFolders"
    
    try:
        response = requests.get(folders_url, headers=headers, timeout=30)
        response.raise_for_status()
        folders_data = response.json()
        folders = folders_data.get("value", [])
        
        print(f"[✓] Found {len(folders)} mail folders:")
        
        inbox_id = None
        for folder in folders:
            folder_name = folder.get("displayName", "Unknown")
            folder_id = folder.get("id", "Unknown")
            total_items = folder.get("totalItemCount", 0)
            unread_items = folder.get("unreadItemCount", 0)
            
            print(f"    - {folder_name}: {total_items} items ({unread_items} unread)")
            
            if folder_name.lower() == TEST_FOLDER.lower():
                inbox_id = folder_id
        
        if not inbox_id:
            print(f"\n[✗] '{TEST_FOLDER}' folder not found")
            print("    Available folders listed above")
            sys.exit(1)
        
        print(f"\n[✓] Found '{TEST_FOLDER}' folder ID: {inbox_id[:40]}...")
        
    except requests.exceptions.HTTPError as e:
        print(f"[✗] Failed to access mailbox: {e}")
        print(f"    Response: {e.response.json()}")
        sys.exit(1)
    
    # Test 3: Fetch sample emails
    print(f"\n[4/4] Fetching {TEST_MAX_EMAILS} sample emails from last year...")
    
    from datetime import datetime, timedelta
    
    # Calculate date filter (last year)
    now = datetime.now()
    start_date = now - timedelta(days=365)
    date_filter = f"receivedDateTime ge {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    
    messages_url = f"{base_url}/users/{TEST_EMAIL}/mailFolders/{inbox_id}/messages"
    params = {
        "$top": TEST_MAX_EMAILS,
        "$select": "subject,from,receivedDateTime,hasAttachments",
        "$orderby": "receivedDateTime desc",
        "$filter": date_filter
    }
    
    try:
        response = requests.get(messages_url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        emails_data = response.json()
        emails = emails_data.get("value", [])
        
        print(f"[✓] Retrieved {len(emails)} emails")
        
        if emails:
            print(f"\n{'=' * 80}")
            print(f"  SAMPLE EMAILS FROM {TEST_FOLDER}")
            print(f"{'=' * 80}\n")
            
            for i, email in enumerate(emails, 1):
                subject = email.get('subject', 'No Subject')
                from_email = email.get('from', {}).get('emailAddress', {})
                from_name = from_email.get('name', 'Unknown')
                from_addr = from_email.get('address', 'Unknown')
                received_date = email.get('receivedDateTime', '')
                has_attachments = email.get('hasAttachments', False)
                
                if received_date:
                    try:
                        dt = datetime.fromisoformat(received_date.replace('Z', '+00:00'))
                        received_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                print(f"[{i}] {subject}")
                print(f"    From: {from_name} <{from_addr}>")
                print(f"    Date: {received_date}")
                print(f"    Attachments: {'Yes' if has_attachments else 'No'}")
                print()
        else:
            print(f"\n[!] No emails found in {TEST_FOLDER} from last year")
            print("    The folder might be empty or all emails are older than 1 year")
        
        print("=" * 80)
        print("  TEST COMPLETE - SUCCESS!")
        print("=" * 80)
        print(f"\n✅ Configuration is correct:")
        print(f"   Email: {TEST_EMAIL}")
        print(f"   Folder: {TEST_FOLDER}")
        print(f"   Emails found: {len(emails)}")
        print(f"\nYou can now use these settings for full rebuild:")
        print(f"   OUTLOOK_USER_EMAIL={TEST_EMAIL}")
        print(f"   OUTLOOK_FOLDER_NAME={TEST_FOLDER}")
        print(f"   OUTLOOK_DATE_FILTER=last_year")
        
    except requests.exceptions.HTTPError as e:
        print(f"[✗] Failed to fetch emails: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"    Response: {e.response.json()}")
        sys.exit(1)

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

