#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick connectivity test - Only blogs and emails
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("  QUICK CONNECTIVITY TEST")
print("=" * 80)

# Test 1: Blogs
print("\n[1/2] Testing Blog Connectivity...")
try:
    from app.helpers import fetch_posts
    blog_api_url = "https://cloudfuze.com/wp-json/wp/v2/posts"
    posts = fetch_posts(blog_api_url, per_page=3, max_pages=1)
    print(f"[✓] Blogs: {len(posts)} posts fetched")
except Exception as e:
    print(f"[✗] Blogs: Failed - {e}")

# Test 2: Emails
print("\n[2/2] Testing Outlook Connectivity...")
try:
    from app.outlook_processor import OutlookProcessor
    from config import OUTLOOK_FOLDER_NAME
    
    processor = OutlookProcessor()
    emails = processor.get_emails_from_folder(
        folder_name=OUTLOOK_FOLDER_NAME,
        max_emails=5
    )
    
    threads = processor.group_emails_by_conversation(emails)
    print(f"[✓] Outlook: {len(emails)} emails in {len(threads)} threads")
except Exception as e:
    print(f"[✗] Outlook: Failed - {e}")

print("\n" + "=" * 80)
print("  QUICK TEST COMPLETE")
print("=" * 80)
print("\nReady to proceed with FULL REBUILD!")
print("Run: python server.py (with INITIALIZE_VECTORSTORE=true)")

