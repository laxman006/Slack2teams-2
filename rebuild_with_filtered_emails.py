#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete rebuild with filtered emails
Blogs + SharePoint + Filtered Emails (presalesteam@cloudfuze.com only, last 12 months)
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Set environment variables for filtered email ingestion
os.environ['OUTLOOK_USER_EMAIL'] = 'presales@cloudfuze.com'
os.environ['OUTLOOK_FOLDER_NAME'] = 'Inbox'
os.environ['OUTLOOK_DATE_FILTER'] = 'last_12_months'
os.environ['OUTLOOK_MAX_EMAILS'] = '10000'
os.environ['OUTLOOK_FILTER_EMAIL'] = 'presalesteam@cloudfuze.com'  # NEW: Filter emails

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  REBUILD WITH FILTERED EMAILS")
print("=" * 80)
print("\nSources:")
print("  1. Blogs: ALL from cloudfuze.com")
print("  2. SharePoint: ALL files from DOC360")
print("  3. Emails: FILTERED - only involving presalesteam@cloudfuze.com")
print("     - Mailbox: presales@cloudfuze.com")
print("     - Folder: Inbox")
print("     - Time: Last 12 months")
print("=" * 80)

try:
    from app.vectorstore import check_and_rebuild_if_needed
    from config import ENABLE_WEB_SOURCE, ENABLE_SHAREPOINT_SOURCE, ENABLE_OUTLOOK_SOURCE
    
    print(f"\nConfiguration check:")
    print(f"  WEB_SOURCE: {ENABLE_WEB_SOURCE}")
    print(f"  SHAREPOINT_SOURCE: {ENABLE_SHAREPOINT_SOURCE}")
    print(f"  OUTLOOK_SOURCE: {ENABLE_OUTLOOK_SOURCE}")
    
    if not all([ENABLE_WEB_SOURCE, ENABLE_SHAREPOINT_SOURCE, ENABLE_OUTLOOK_SOURCE]):
        print("\n[!] WARNING: Some sources are disabled in .env")
    
    print("\n[*] Starting vectorstore rebuild...")
    print("    This will take 15-30 minutes...")
    print()
    
    # Force rebuild
    check_and_rebuild_if_needed(force_rebuild=True)
    
    print("\n" + "=" * 80)
    print("  REBUILD COMPLETE!")
    print("=" * 80)

except Exception as e:
    print(f"\n[✗] Rebuild failed: {e}")
    import traceback
    traceback.print_exc()

