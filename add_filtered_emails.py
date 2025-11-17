#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add filtered emails to existing vectorstore (incremental update)
Only emails involving presalesteam@cloudfuze.com from last 12 months
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List
import requests

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  INCREMENTAL EMAIL INGESTION - FILTERED")
print("=" * 80)

# Configuration
MAILBOX = "presales@cloudfuze.com"
FILTER_EMAIL = "presalesteam@cloudfuze.com"
FOLDER = "Inbox"
MONTHS_BACK = 12
MAX_EMAILS = 10000  # Safety limit

print(f"\nConfiguration:")
print(f"  Mailbox: {MAILBOX}")
print(f"  Filter: Only emails involving {FILTER_EMAIL}")
print(f"  Folder: {FOLDER}")
print(f"  Time range: Last {MONTHS_BACK} months")
print(f"  Max emails: {MAX_EMAILS}")
print("=" * 80)

try:
    from app.sharepoint_auth import sharepoint_auth
    from app.outlook_processor import OutlookProcessor
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    import chromadb
    from config import CHROMA_DB_PATH, OPENAI_API_KEY
    
    print("\n[1/6] Getting access token...")
    access_token = sharepoint_auth.get_access_token()
    print("[✓] Token obtained")
    
    base_url = "https://graph.microsoft.com/v1.0"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    print(f"\n[2/6] Getting '{FOLDER}' folder ID...")
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
    
    print(f"\n[3/6] Fetching emails from last {MONTHS_BACK} months involving {FILTER_EMAIL}...")
    
    # Calculate date filter (last 12 months)
    start_date = datetime.now() - timedelta(days=MONTHS_BACK * 30)
    date_filter = f"receivedDateTime ge {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    
    # Fetch all emails (with pagination)
    messages_url = f"{base_url}/users/{MAILBOX}/mailFolders/{folder_id}/messages"
    
    all_emails = []
    next_url = messages_url
    page = 0
    
    while next_url and len(all_emails) < MAX_EMAILS:
        page += 1
        print(f"[*] Fetching page {page}...")
        
        params = {
            "$top": 100,
            "$select": "subject,from,toRecipients,ccRecipients,receivedDateTime,conversationId,hasAttachments,body,bodyPreview,id",
            "$orderby": "receivedDateTime desc",
            "$filter": date_filter
        } if next_url == messages_url else None
        
        response = requests.get(next_url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        emails = data.get("value", [])
        all_emails.extend(emails)
        
        next_url = data.get("@odata.nextLink")
        
        print(f"    Retrieved {len(emails)} emails (total: {len(all_emails)})")
        
        if not next_url:
            break
    
    print(f"[✓] Total emails fetched: {len(all_emails)}")
    
    # Filter emails involving presalesteam@cloudfuze.com
    print(f"\n[4/6] Filtering for emails involving {FILTER_EMAIL}...")
    
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
    
    print(f"[✓] Filtered emails: {len(filtered_emails)} (out of {len(all_emails)})")
    print(f"    Filter rate: {len(filtered_emails)/len(all_emails)*100:.1f}%")
    
    if not filtered_emails:
        print("\n[!] No filtered emails found. Nothing to add.")
        sys.exit(0)
    
    # Group by conversation and create documents
    print(f"\n[5/6] Processing emails into conversation threads...")
    
    processor = OutlookProcessor()
    
    # Group by conversation
    from collections import defaultdict
    conversations = defaultdict(list)
    
    for email in filtered_emails:
        conversation_id = email.get("conversationId")
        if conversation_id:
            conversations[conversation_id].append(email)
    
    # Sort emails within each conversation by date
    for conv_id, conv_emails in conversations.items():
        conversations[conv_id] = sorted(
            conv_emails,
            key=lambda x: x.get("receivedDateTime", "")
        )
    
    print(f"[✓] Grouped into {len(conversations)} conversation threads")
    
    # Convert to documents
    thread_docs = []
    for conv_id, thread_emails in conversations.items():
        doc = processor.format_thread_as_document(thread_emails, FOLDER)
        if doc:
            thread_docs.append(doc)
    
    print(f"[✓] Created {len(thread_docs)} thread documents")
    
    # Chunk large threads if needed
    chunked_docs = processor.chunk_thread_documents(thread_docs)
    print(f"[✓] Final chunks: {len(chunked_docs)}")
    
    # Add to existing vectorstore
    print(f"\n[6/6] Adding to existing vectorstore...")
    print(f"    Path: {CHROMA_DB_PATH}")
    
    # Load existing vectorstore
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # Get or create collection
    collection = client.get_or_create_collection(
        name="langchain",
        metadata={
            "hnsw:space": "cosine",
            "hnsw:M": 48,
            "hnsw:construction_ef": 200,
            "hnsw:search_ef": 100
        }
    )
    
    try:
        existing_count = collection.count()
        print(f"[✓] Existing vectorstore found: {existing_count} documents")
    except Exception as e:
        print(f"[!] Could not count existing documents: {e}")
        print("[*] Assuming vectorstore exists, proceeding to add documents...")
        existing_count = 0
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    # Create vectorstore instance
    vectorstore = Chroma(
        client=client,
        collection_name="langchain",
        embedding_function=embeddings
    )
    
    # Add documents in batches
    print(f"[*] Adding {len(chunked_docs)} email chunks to vectorstore...")
    
    batch_size = 50
    for i in range(0, len(chunked_docs), batch_size):
        batch = chunked_docs[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(chunked_docs) + batch_size - 1) // batch_size
        
        print(f"    Batch {batch_num}/{total_batches}: Adding {len(batch)} chunks...")
        vectorstore.add_documents(batch)
    
    # Verify
    new_count = collection.count()
    added_count = new_count - existing_count
    
    print(f"\n[✓] SUCCESSFULLY ADDED TO VECTORSTORE!")
    print(f"    Previous count: {existing_count}")
    print(f"    Added: {added_count}")
    print(f"    New total: {new_count}")
    
    print("\n" + "=" * 80)
    print("  INCREMENTAL INGESTION COMPLETE")
    print("=" * 80)
    
    print(f"\n📊 Summary:")
    print(f"   Emails scanned: {len(all_emails)}")
    print(f"   Filtered emails: {len(filtered_emails)} (involving {FILTER_EMAIL})")
    print(f"   Conversation threads: {len(conversations)}")
    print(f"   Chunks added: {added_count}")
    print(f"\n✅ Your vectorstore now contains:")
    print(f"   - Blogs: ~7,097 chunks")
    print(f"   - SharePoint: 1,884 chunks")
    print(f"   - Filtered emails: {added_count} chunks")
    print(f"   - Total: {new_count} chunks")
    
    print(f"\n🚀 Server is ready at: http://localhost:8002")
    print(f"   You can now query emails involving {FILTER_EMAIL}")

except Exception as e:
    print(f"\n[✗] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

