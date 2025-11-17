#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check Blog and Email Content in Vectorstore
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.vectorstore import vectorstore
    from collections import Counter
    
    print("=" * 80)
    print("  BLOG & EMAIL CONTENT ANALYSIS")
    print("=" * 80)
    
    # Get all documents
    collection = vectorstore._collection
    results = collection.get(limit=10000, include=['metadatas', 'documents'])
    
    # Categorize by source
    blog_chunks = []
    email_chunks = []
    sharepoint_chunks = []
    other_chunks = []
    
    for i, metadata in enumerate(results['metadatas']):
        source_type = metadata.get('source_type', '').lower()
        source = metadata.get('source', '').lower()
        tag = metadata.get('tag', '').lower()
        
        if source_type == 'web' or 'blog' in source or 'blog' in tag:
            blog_chunks.append({
                'metadata': metadata,
                'content': results['documents'][i][:200] + "..."
            })
        elif source_type == 'email' or 'email' in source or 'outlook' in source:
            email_chunks.append({
                'metadata': metadata,
                'content': results['documents'][i][:200] + "..."
            })
        elif source_type == 'sharepoint':
            sharepoint_chunks.append(metadata)
        else:
            other_chunks.append(metadata)
    
    # Print summary
    print(f"\n📊 CONTENT SUMMARY")
    print("=" * 80)
    print(f"   Total Chunks: {len(results['ids'])}")
    print(f"   └─ SharePoint: {len(sharepoint_chunks)} chunks")
    print(f"   └─ Blogs: {len(blog_chunks)} chunks")
    print(f"   └─ Emails: {len(email_chunks)} chunks")
    print(f"   └─ Other: {len(other_chunks)} chunks")
    
    # Detailed blog analysis
    if blog_chunks:
        print(f"\n📝 BLOG POSTS DETAILS")
        print("=" * 80)
        
        # Group by URL to count unique posts
        blog_urls = set()
        for chunk in blog_chunks:
            url = chunk['metadata'].get('url', '')
            if url:
                blog_urls.add(url)
        
        print(f"   Unique Blog Posts: {len(blog_urls)}")
        print(f"   Total Blog Chunks: {len(blog_chunks)}")
        print(f"   Average Chunks per Post: {len(blog_chunks)/max(len(blog_urls), 1):.1f}")
        
        print(f"\n   Blog URLs:")
        for i, url in enumerate(sorted(blog_urls)[:10], 1):
            print(f"   {i}. {url}")
        
        print(f"\n   Sample Blog Chunks:")
        for i, chunk in enumerate(blog_chunks[:3], 1):
            print(f"\n   [{i}] {chunk['metadata'].get('title', 'No title')}")
            print(f"       URL: {chunk['metadata'].get('url', 'N/A')}")
            print(f"       Preview: {chunk['content']}")
    else:
        print(f"\n📝 BLOGS: None found")
    
    # Detailed email analysis
    if email_chunks:
        print(f"\n📧 EMAIL THREADS DETAILS")
        print("=" * 80)
        
        # Group by thread or conversation
        email_threads = set()
        for chunk in email_chunks:
            thread_id = chunk['metadata'].get('thread_id') or chunk['metadata'].get('conversation_id')
            if thread_id:
                email_threads.add(thread_id)
        
        print(f"   Unique Email Threads: {len(email_threads)}")
        print(f"   Total Email Chunks: {len(email_chunks)}")
        
        print(f"\n   Sample Email Chunks:")
        for i, chunk in enumerate(email_chunks[:3], 1):
            print(f"\n   [{i}] Thread: {chunk['metadata'].get('thread_id', 'N/A')}")
            print(f"       From: {chunk['metadata'].get('email_from', 'N/A')}")
            print(f"       Preview: {chunk['content']}")
    else:
        print(f"\n📧 EMAILS: None found")
    
    # Check if they were supposed to be ingested
    print(f"\n" + "=" * 80)
    print("  INGESTION SETTINGS CHECK")
    print("=" * 80)
    
    from config import ENABLE_OUTLOOK_SOURCE, ENABLE_WEB_SOURCE
    print(f"   ENABLE_WEB_SOURCE (Blogs): {ENABLE_WEB_SOURCE}")
    print(f"   ENABLE_OUTLOOK_SOURCE (Emails): {ENABLE_OUTLOOK_SOURCE}")
    
    if not blog_chunks and ENABLE_WEB_SOURCE:
        print(f"\n   ⚠️  Blogs enabled but none found in vectorstore")
        print(f"   → May need to run ingestion with blog source enabled")
    
    if not email_chunks and ENABLE_OUTLOOK_SOURCE:
        print(f"\n   ⚠️  Emails enabled but none found in vectorstore")
        print(f"   → May need to run ingestion with Outlook source enabled")
    
    print("\n" + "=" * 80)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

