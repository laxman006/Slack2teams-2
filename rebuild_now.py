#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick Vectorstore Rebuild Script
Sets environment variables and rebuilds vectorstore
"""

import os
import shutil
from datetime import datetime

# Set environment variables BEFORE importing app modules
os.environ["INITIALIZE_VECTORSTORE"] = "true"
os.environ["ENABLE_WEB_SOURCE"] = "true"
os.environ["ENABLE_SHAREPOINT_SOURCE"] = "true"
# Add others as needed:
# os.environ["ENABLE_PDF_SOURCE"] = "true"
# os.environ["ENABLE_EXCEL_SOURCE"] = "true"
# os.environ["ENABLE_DOC_SOURCE"] = "true"

from dotenv import load_dotenv
load_dotenv()

from config import CHROMA_DB_PATH
from app.helpers import build_combined_vectorstore, fetch_web_content
from app.sharepoint_processor import process_sharepoint_content

def rebuild():
    """Rebuild vectorstore with corrected tags."""
    print("=" * 70)
    print("VECTORSTORE REBUILD - With Corrected Tags")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Remove existing vectorstore
    if os.path.exists(CHROMA_DB_PATH):
        print(f"[*] Removing existing vectorstore: {CHROMA_DB_PATH}")
        shutil.rmtree(CHROMA_DB_PATH)
        print("[OK] Removed")
    
    print("\n[*] Building vectorstore from sources:")
    print("    ✓ Web/Blog Posts (tag: 'blog')")
    print("    ✓ SharePoint (tag: hierarchical folder paths)")
    print()
    
    # Build vectorstore
    print("[*] Starting rebuild...")
    print()
    
    try:
        # Get CloudFuze blog URL from config
        from config import WEB_SOURCE_URL
        
        vectorstore = build_combined_vectorstore(
            url=WEB_SOURCE_URL,
            pdf_directory=None,  # Disable if not needed
            excel_directory=None,  # Disable if not needed
            doc_directory=None,  # Disable if not needed
            sharepoint_enabled=True
        )
        
        if vectorstore:
            doc_count = vectorstore._collection.count()
            print()
            print("=" * 70)
            print("✓✓✓ REBUILD COMPLETE!")
            print("=" * 70)
            print(f"Total documents: {doc_count}")
            print(f"Location: {CHROMA_DB_PATH}")
            print()
            
            # Verify tags
            print("[*] Verifying tags...")
            test_results = vectorstore.similarity_search("CloudFuze", k=5)
            
            tags_found = set()
            for doc in test_results:
                tag = doc.metadata.get('tag', 'no tag')
                tags_found.add(tag)
            
            print(f"[OK] Tags found: {', '.join(sorted(tags_found))}")
            print()
            print("Sample documents:")
            for i, doc in enumerate(test_results[:3], 1):
                tag = doc.metadata.get('tag', 'no tag')
                source = doc.metadata.get('source_type', 'unknown')
                title = doc.metadata.get('post_title', doc.metadata.get('file_name', ''))[:50]
                print(f"  {i}. [{tag}] {source}: {title}...")
            
            print()
            print("✓ Vectorstore ready with corrected tags!")
            return 0
        else:
            print("[ERROR] Rebuild failed - no vectorstore created")
            return 1
            
    except Exception as e:
        print(f"[ERROR] Rebuild failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(rebuild())

