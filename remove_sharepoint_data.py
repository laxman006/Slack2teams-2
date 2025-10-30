#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Remove SharePoint documents from vectorstore.

This script deletes all documents with source_type="sharepoint" from the ChromaDB vectorstore.
Use this before re-extracting SharePoint data to avoid duplicates.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CHROMA_DB_PATH
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

def remove_sharepoint_documents():
    """Remove all SharePoint documents from the vectorstore."""
    print("=" * 60)
    print("REMOVING SHAREPOINT DOCUMENTS FROM VECTORSTORE")
    print("=" * 60)
    
    # Check if vectorstore exists
    if not os.path.exists(CHROMA_DB_PATH):
        print("[INFO] Vectorstore not found. Nothing to remove.")
        return
    
    try:
        # Load existing vectorstore
        print("[*] Loading vectorstore...")
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings
        )
        
        # Get collection
        collection = vectorstore._collection
        
        # Get total count before deletion for reporting
        try:
            total_before = collection.count()
            print(f"[INFO] Total documents in vectorstore: {total_before}")
        except:
            total_before = None
        
        # Delete SharePoint documents directly (skip slow counting step)
        where_clause = {"source_type": "sharepoint"}
        print("[*] Deleting SharePoint documents...")
        print("   [INFO] This may take a moment for large vectorstores...")
        try:
            result = collection.delete(where=where_clause)
            print(f"[OK] SharePoint documents deletion completed")
        except Exception as e:
            print(f"[ERROR] Failed to delete SharePoint documents: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Get total document count after deletion
        try:
            total_after = collection.count()
            print(f"[INFO] Total documents remaining in vectorstore: {total_after}")
            if total_before:
                deleted_count = total_before - total_after
                print(f"[INFO] Estimated SharePoint documents deleted: {deleted_count}")
        except Exception as e:
            print(f"[INFO] Could not get final count: {e}")
        
        # Quick verification (skip slow get() call)
        print("[OK] Deletion completed successfully")
        
        print("=" * 60)
        print("[OK] SharePoint documents removal complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run your server: python server.py")
        print("2. SharePoint extraction will run and add fresh documents")
        print("3. No duplicates will be created\n")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error removing SharePoint documents: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = remove_sharepoint_documents()
    sys.exit(0 if success else 1)

