#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Update Outlook emails with correct date filter
Removes old email chunks and adds new ones with last_year filter
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Update environment BEFORE importing anything else
import os
os.environ['OUTLOOK_DATE_FILTER'] = 'last_year'

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  OUTLOOK DATE FILTER UPDATE")
print("=" * 80)

try:
    import chromadb
    from config import CHROMA_DB_PATH
    
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection("langchain")
    
    initial_count = collection.count()
    print(f"\nInitial vectorstore size: {initial_count:,} chunks")
    
    # Count current email chunks
    print("\n[*] Counting existing email chunks...")
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
    
    print(f"[OK] Found {len(email_ids)} email chunks to remove")
    print(f"    (These are from the last 10 days only)")
    
    if email_ids:
        print(f"\n[*] Removing old email chunks...")
        # Delete in batches to avoid overwhelming the DB
        batch_size = 500
        for i in range(0, len(email_ids), batch_size):
            batch = email_ids[i:i+batch_size]
            collection.delete(ids=batch)
            print(f"    Deleted batch {i//batch_size + 1}/{(len(email_ids)-1)//batch_size + 1}")
        
        print(f"[OK] Removed {len(email_ids)} old email chunks")
    
    after_delete_count = collection.count()
    print(f"\nAfter deletion: {after_delete_count:,} chunks")
    print(f"  Blogs: ~{7097} (preserved)")
    print(f"  SharePoint: ~{1873} (preserved)")
    print(f"  Emails: 0 (removed)")
    
    # Now fetch new emails with last_year filter
    print("\n" + "=" * 80)
    print("  FETCHING EMAILS WITH LAST_YEAR FILTER")
    print("=" * 80)
    
    from app.outlook_processor import process_outlook_content
    
    print("\n[*] Processing Outlook emails with 'last_year' filter...")
    print("    This will scan the last 12 months...")
    print("    Filter: presalesteam@cloudfuze.com")
    
    new_email_docs = process_outlook_content()
    
    if not new_email_docs:
        print("\n[WARNING] No new emails fetched!")
        print("          Check the configuration and try again")
        sys.exit(1)
    
    print(f"\n[OK] Fetched {len(new_email_docs)} new email chunks")
    
    # Add new emails to vectorstore
    print("\n[*] Adding new emails to vectorstore...")
    
    from langchain_openai import OpenAIEmbeddings
    from config import OPENAI_API_KEY
    
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    # Generate embeddings and add in batches
    batch_size = 50
    total_batches = (len(new_email_docs) - 1) // batch_size + 1
    
    for i in range(0, len(new_email_docs), batch_size):
        batch = new_email_docs[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        print(f"   [*] Adding batch {batch_num}/{total_batches} ({len(batch)} documents)...")
        
        # Generate embeddings for batch
        texts = [doc.page_content for doc in batch]
        batch_embeddings = embeddings.embed_documents(texts)
        
        # Add to collection with embeddings
        collection.add(
            documents=texts,
            metadatas=[doc.metadata for doc in batch],
            embeddings=batch_embeddings,
            ids=[f"email_new_{i+j}" for j in range(len(batch))]
        )
    
    final_count = collection.count()
    print(f"\n[OK] Successfully added all {len(new_email_docs)} email chunks!")
    
    # Update metadata file
    print("\n[*] Updating vectorstore metadata...")
    from app.vectorstore import get_current_metadata
    import json
    
    metadata = get_current_metadata()
    with open("./data/vectorstore_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("[OK] Metadata updated")
    
    # Final summary
    print("\n" + "=" * 80)
    print("  UPDATE COMPLETE")
    print("=" * 80)
    
    print(f"\nVectorstore Summary:")
    print(f"  Before: {initial_count:,} chunks")
    print(f"  After:  {final_count:,} chunks")
    print(f"  Change: +{final_count - initial_count:,} chunks")
    
    print(f"\nBreakdown (estimated):")
    print(f"  Blogs: 7,097 chunks")
    print(f"  SharePoint: 1,873 chunks")
    print(f"  Emails: {len(new_email_docs)} chunks (LAST YEAR)")
    
    print(f"\n✅ Outlook emails updated successfully!")
    print(f"   Old: Last 10 days only")
    print(f"   New: Last 12 months (365 days)")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)

