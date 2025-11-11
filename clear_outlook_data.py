# -*- coding: utf-8 -*-
"""
Clear Outlook Email Data from Vectorstore

This script removes all Outlook email documents from the vectorstore
without affecting other sources (blog posts, SharePoint, PDFs, etc.).

Usage:
    python clear_outlook_data.py
"""

import os
import shutil
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import CHROMA_DB_PATH

def clear_outlook_from_vectorstore():
    """Remove all Outlook email documents from vectorstore."""
    print("=" * 60)
    print("CLEAR OUTLOOK EMAIL DATA FROM VECTORSTORE")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if vectorstore exists
    if not os.path.exists(CHROMA_DB_PATH):
        print("[!] No vectorstore found at:", CHROMA_DB_PATH)
        print("[!] Nothing to clean.")
        return
    
    print(f"[*] Loading vectorstore from: {CHROMA_DB_PATH}")
    
    try:
        # Load vectorstore
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings
        )
        
        # Get total document count
        total_docs = vectorstore._collection.count()
        print(f"[*] Current total documents: {total_docs}")
        
        # Get all documents with metadata
        print("[*] Scanning for Outlook email documents...")
        all_docs = vectorstore._collection.get(include=['metadatas'])
        
        # Find Outlook document IDs
        outlook_ids = []
        for idx, metadata in enumerate(all_docs['metadatas']):
            source_type = metadata.get('source_type', '')
            tag = metadata.get('tag', '')
            
            # Identify Outlook documents
            if source_type == 'outlook' or tag.startswith('email/'):
                outlook_ids.append(all_docs['ids'][idx])
        
        if not outlook_ids:
            print("[OK] No Outlook email documents found in vectorstore")
            print("[OK] Nothing to clean")
            return
        
        print(f"[*] Found {len(outlook_ids)} Outlook email documents to remove")
        
        # Confirm deletion
        print()
        print("⚠️  WARNING: This will permanently delete Outlook email data!")
        print(f"   Documents to delete: {len(outlook_ids)}")
        print(f"   Documents remaining: {total_docs - len(outlook_ids)}")
        print()
        
        confirm = input("Continue with deletion? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("[!] Deletion cancelled by user")
            return
        
        # Delete Outlook documents
        print()
        print("[*] Deleting Outlook email documents...")
        
        # Delete in batches to avoid issues
        batch_size = 100
        deleted_count = 0
        
        for i in range(0, len(outlook_ids), batch_size):
            batch = outlook_ids[i:i + batch_size]
            vectorstore._collection.delete(ids=batch)
            deleted_count += len(batch)
            print(f"   [*] Deleted {deleted_count}/{len(outlook_ids)} documents...")
        
        # Verify deletion
        remaining_docs = vectorstore._collection.count()
        print()
        print("[OK] Deletion complete!")
        print(f"   Before: {total_docs} documents")
        print(f"   Deleted: {len(outlook_ids)} documents")
        print(f"   After: {remaining_docs} documents")
        
        # Update metadata file to remove outlook source
        update_metadata_file()
        
        print()
        print("=" * 60)
        print("[✓] OUTLOOK DATA CLEARED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Set INITIALIZE_VECTORSTORE=true in .env")
        print("2. Run: python server.py")
        print("3. Outlook emails will be re-indexed with new format")
        print()
        
    except Exception as e:
        print(f"[ERROR] Failed to clear Outlook data: {e}")
        import traceback
        traceback.print_exc()

def update_metadata_file():
    """Update metadata file to remove outlook source."""
    metadata_file = "./data/vectorstore_metadata.json"
    
    if not os.path.exists(metadata_file):
        print("[*] No metadata file found - will be recreated on rebuild")
        return
    
    try:
        import json
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Remove outlook from enabled sources
        if 'enabled_sources' in metadata:
            if 'outlook' in metadata['enabled_sources']:
                metadata['enabled_sources'].remove('outlook')
        
        # Remove outlook metadata
        if 'outlook' in metadata:
            del metadata['outlook']
        
        # Update timestamp
        metadata['timestamp'] = datetime.now().isoformat()
        
        # Save updated metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print("[OK] Updated metadata file - Outlook source removed")
        
    except Exception as e:
        print(f"[WARNING] Could not update metadata file: {e}")
        print("[*] You may want to delete it manually: ./data/vectorstore_metadata.json")

def clear_entire_vectorstore():
    """Nuclear option: Delete entire vectorstore."""
    print("=" * 60)
    print("⚠️  CLEAR ENTIRE VECTORSTORE (ALL SOURCES)")
    print("=" * 60)
    print()
    print("This will delete ALL data from the vectorstore:")
    print("- Blog posts")
    print("- SharePoint documents")
    print("- PDF files")
    print("- Excel files")
    print("- Word documents")
    print("- Outlook emails")
    print()
    
    confirm = input("Are you SURE you want to delete EVERYTHING? (type 'DELETE ALL'): ").strip()
    
    if confirm != 'DELETE ALL':
        print("[!] Cancelled - vectorstore preserved")
        return
    
    try:
        if os.path.exists(CHROMA_DB_PATH):
            shutil.rmtree(CHROMA_DB_PATH)
            print("[OK] Vectorstore deleted:", CHROMA_DB_PATH)
        
        metadata_file = "./data/vectorstore_metadata.json"
        if os.path.exists(metadata_file):
            os.remove(metadata_file)
            print("[OK] Metadata file deleted:", metadata_file)
        
        print()
        print("[✓] Complete vectorstore cleared!")
        print()
        print("To rebuild:")
        print("1. Set INITIALIZE_VECTORSTORE=true")
        print("2. Enable sources you want (ENABLE_WEB_SOURCE, etc.)")
        print("3. Run: python server.py")
        
    except Exception as e:
        print(f"[ERROR] Failed to clear vectorstore: {e}")

if __name__ == "__main__":
    import sys
    
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        Outlook Email Data Cleanup Utility                 ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print("Choose an option:")
    print()
    print("1. Clear ONLY Outlook email data (recommended)")
    print("2. Clear ENTIRE vectorstore (all sources)")
    print("3. Cancel")
    print()
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        clear_outlook_from_vectorstore()
    elif choice == "2":
        clear_entire_vectorstore()
    elif choice == "3":
        print("[!] Cancelled - no changes made")
    else:
        print("[!] Invalid choice - exiting")
    
    print()

