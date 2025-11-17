#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Show all ingested email threads from vectorstore
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  INGESTED EMAIL THREADS REPORT")
print("=" * 80)

try:
    import chromadb
    from config import CHROMA_DB_PATH
    from datetime import datetime
    
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection("langchain")
    
    # Get all email chunks
    print("\n[*] Fetching all email data...")
    
    total_count = collection.count()
    batch_size = 1000
    all_email_metadatas = []
    
    for offset in range(0, total_count, batch_size):
        limit = min(batch_size, total_count - offset)
        results = collection.get(
            limit=limit,
            offset=offset,
            include=['metadatas']
        )
        if results and 'metadatas' in results:
            email_metas = [m for m in results['metadatas'] 
                          if m and m.get('source_type') == 'outlook']
            all_email_metadatas.extend(email_metas)
    
    print(f"[OK] Found {len(all_email_metadatas)} email chunks")
    
    # Group by conversation
    conversations = defaultdict(list)
    for meta in all_email_metadatas:
        conv_id = meta.get('conversation_id', 'unknown')
        conversations[conv_id].append(meta)
    
    print(f"[OK] Grouped into {len(conversations)} conversation threads")
    
    print("\n" + "=" * 80)
    print("  EMAIL THREADS DETAILS")
    print("=" * 80)
    
    # Sort by date
    thread_list = []
    for conv_id, metas in conversations.items():
        # Get first metadata (they should all be similar for same thread)
        meta = metas[0]
        
        thread_info = {
            'subject': meta.get('conversation_topic', 'No Subject'),
            'participants': meta.get('participants', ''),
            'email_count': meta.get('email_count', 0),
            'first_date': meta.get('first_email_date', ''),
            'last_date': meta.get('last_email_date', ''),
            'date_range': meta.get('date_range', ''),
            'folder': meta.get('folder_name', ''),
            'chunks': len(metas)
        }
        thread_list.append(thread_info)
    
    # Sort by last date (most recent first)
    thread_list.sort(key=lambda x: x['last_date'], reverse=True)
    
    # Display all threads
    for i, thread in enumerate(thread_list, 1):
        print(f"\n{'=' * 80}")
        print(f"Thread #{i}")
        print(f"{'=' * 80}")
        print(f"Subject: {thread['subject'][:150]}")
        if len(thread['subject']) > 150:
            print(f"         ...{thread['subject'][-50:]}")
        print(f"\nParticipants:")
        participants = thread['participants'].split(', ')
        for p in participants[:10]:  # Show first 10
            print(f"  • {p}")
        if len(participants) > 10:
            print(f"  • ... and {len(participants) - 10} more")
        
        print(f"\nDetails:")
        print(f"  • Emails in thread: {thread['email_count']}")
        print(f"  • Date range: {thread['date_range']}")
        print(f"  • First email: {thread['first_date']}")
        print(f"  • Last email: {thread['last_date']}")
        print(f"  • Folder: {thread['folder']}")
        print(f"  • Vector chunks: {thread['chunks']}")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("  SUMMARY STATISTICS")
    print("=" * 80)
    
    total_emails = sum(t['email_count'] for t in thread_list)
    total_chunks = sum(t['chunks'] for t in thread_list)
    avg_emails_per_thread = total_emails / len(thread_list) if thread_list else 0
    avg_chunks_per_thread = total_chunks / len(thread_list) if thread_list else 0
    
    print(f"\nTotal conversation threads: {len(thread_list)}")
    print(f"Total emails: {total_emails}")
    print(f"Total vector chunks: {total_chunks}")
    print(f"Average emails per thread: {avg_emails_per_thread:.1f}")
    print(f"Average chunks per thread: {avg_chunks_per_thread:.1f}")
    
    # Date range
    if thread_list:
        all_dates = [t['last_date'] for t in thread_list if t['last_date']]
        if all_dates:
            earliest = min(all_dates)
            latest = max(all_dates)
            print(f"\nDate range of threads:")
            print(f"  Earliest: {earliest}")
            print(f"  Latest: {latest}")
    
    # Check for presalesteam@cloudfuze.com in participants
    print(f"\n{'=' * 80}")
    print("  FILTER VERIFICATION")
    print(f"{'=' * 80}")
    
    presales_count = 0
    for thread in thread_list:
        if 'presalesteam@cloudfuze.com' in thread['participants'].lower():
            presales_count += 1
    
    print(f"\nThreads involving presalesteam@cloudfuze.com: {presales_count}/{len(thread_list)}")
    print(f"Filter accuracy: {presales_count/len(thread_list)*100:.1f}%")
    
    if presales_count < len(thread_list):
        print(f"\n⚠️  Warning: {len(thread_list) - presales_count} threads don't contain presalesteam@")
        print("   (This might be okay if they were in CC/BCC)")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

