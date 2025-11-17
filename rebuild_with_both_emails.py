#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rebuild emails with BOTH pre-sales@ and presalesteam@ for full year
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import os
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  REBUILD EMAILS WITH BOTH ADDRESSES")
print("=" * 80)

# Verify configuration
print("\n[*] Configuration:")
print(f"  User: {os.getenv('OUTLOOK_USER_EMAIL')}")
print(f"  Folder: {os.getenv('OUTLOOK_FOLDER_NAME')}")
print(f"  Date Filter: {os.getenv('OUTLOOK_DATE_FILTER')}")
print(f"  Filter Emails: {os.getenv('OUTLOOK_FILTER_EMAIL')}")

filter_emails = os.getenv('OUTLOOK_FILTER_EMAIL', '').split(',')
print(f"\n  Will capture emails involving:")
for email in filter_emails:
    print(f"    • {email.strip()}")

try:
    import chromadb
    from config import CHROMA_DB_PATH
    
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection("langchain")
    
    initial_count = collection.count()
    print(f"\n[*] Current vectorstore: {initial_count:,} chunks")
    
    # Remove existing email chunks (if any)
    print("\n[*] Checking for existing email chunks...")
    batch_size = 1000
    email_ids = []
    
    for offset in range(0, initial_count, batch_size):
        limit = min(batch_size, initial_count - offset)
        results = collection.get(
            limit=limit,
            offset=offset,
            include=['metadatas']
        )
        if results and 'metadatas' in results and 'ids' in results:
            for i, meta in enumerate(results['metadatas']):
                if meta and meta.get('source_type') == 'outlook':
                    email_ids.append(results['ids'][i])
    
    if email_ids:
        print(f"[*] Removing {len(email_ids)} old email chunks...")
        batch_size = 500
        for i in range(0, len(email_ids), batch_size):
            batch = email_ids[i:i+batch_size]
            collection.delete(ids=batch)
        print(f"[OK] Removed {len(email_ids)} old chunks")
    else:
        print("[OK] No old email chunks found")
    
    # Fetch new emails with both filters
    print("\n" + "=" * 80)
    print("  FETCHING EMAILS WITH BOTH ADDRESSES")
    print("=" * 80)
    
    from app.outlook_processor import process_outlook_content
    
    new_email_docs = process_outlook_content()
    
    if not new_email_docs:
        print("\n[WARNING] No emails fetched!")
        sys.exit(1)
    
    print(f"\n[OK] Fetched {len(new_email_docs)} email chunks")
    
    # Add to vectorstore
    print("\n[*] Adding emails to vectorstore...")
    
    from langchain_openai import OpenAIEmbeddings
    from config import OPENAI_API_KEY
    
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    batch_size = 50
    total_batches = (len(new_email_docs) - 1) // batch_size + 1
    
    for i in range(0, len(new_email_docs), batch_size):
        batch = new_email_docs[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        print(f"   [*] Batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
        
        # Generate embeddings
        texts = [doc.page_content for doc in batch]
        batch_embeddings = embeddings.embed_documents(texts)
        
        # Add to collection
        collection.add(
            documents=texts,
            metadatas=[doc.metadata for doc in batch],
            embeddings=batch_embeddings,
            ids=[f"email_both_{i+j}" for j in range(len(batch))]
        )
    
    final_count = collection.count()
    print(f"\n[OK] Successfully added {len(new_email_docs)} email chunks!")
    
    # Update metadata
    print("\n[*] Updating vectorstore metadata...")
    from app.vectorstore import get_current_metadata
    import json
    
    metadata = get_current_metadata()
    with open("./data/vectorstore_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("[OK] Metadata updated")
    
    # Summary
    print("\n" + "=" * 80)
    print("  REBUILD COMPLETE")
    print("=" * 80)
    
    print(f"\n📊 Vectorstore Summary:")
    print(f"  Before: {initial_count:,} chunks")
    print(f"  After:  {final_count:,} chunks")
    print(f"  Change: +{final_count - initial_count:,} chunks")
    
    print(f"\n📧 Email Coverage:")
    print(f"  • pre-sales@cloudfuze.com (old address)")
    print(f"  • presalesteam@cloudfuze.com (new distribution list)")
    print(f"  • Date range: Last year (365 days)")
    print(f"  • Total email chunks: {len(new_email_docs)}")
    
    print(f"\n✅ SUCCESS!")
    print(f"   Vectorstore now has full year of presales emails")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)

