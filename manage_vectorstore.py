#!/usr/bin/env python3
"""
Manual Vectorstore Management Script

This script allows you to manually manage the vectorstore without automatic initialization.
Use this to control when the expensive blog content loading happens.

Usage:
    python manage_vectorstore.py status    # Check current status
    python manage_vectorstore.py rebuild   # Rebuild vectorstore
    python manage_vectorstore.py clear     # Clear existing vectorstore
"""

import sys
import os
import json
from datetime import datetime

def check_status():
    """Check current vectorstore status."""
    from config import CHROMA_DB_PATH
    from app.vectorstore import load_stored_metadata, get_current_metadata
    
    print("=" * 60)
    print("VECTORSTORE STATUS CHECK")
    print("=" * 60)
    
    # Check if vectorstore exists
    vectorstore_exists = os.path.exists(CHROMA_DB_PATH)
    print(f"Vectorstore exists: {vectorstore_exists}")
    
    if vectorstore_exists:
        try:
            from app.vectorstore import load_existing_vectorstore
            vectorstore = load_existing_vectorstore()
            if vectorstore:
                doc_count = vectorstore._collection.count()
                print(f"Document count: {doc_count}")
            else:
                print("Document count: Failed to load")
        except Exception as e:
            print(f"Error loading vectorstore: {e}")
    
    # Get metadata
    stored_metadata = load_stored_metadata()
    current_metadata = get_current_metadata()
    
    if stored_metadata:
        print(f"Last updated: {stored_metadata.get('timestamp', 'Unknown')}")
        print(f"Blog URL: {stored_metadata.get('url', 'Unknown')}")
    else:
        print("No stored metadata found")
    
    print("=" * 60)

def rebuild_vectorstore():
    """Manually rebuild the vectorstore."""
    print("=" * 60)
    print("MANUAL VECTORSTORE REBUILD")
    print("=" * 60)
    print("⚠️  WARNING: This will cost $16-20 in OpenAI API calls!")
    print("This will fetch and process all blog content from CloudFuze.")
    
    response = input("Do you want to continue? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("Rebuild cancelled.")
        return
    
    try:
        from app.vectorstore import rebuild_vectorstore_if_needed, save_metadata, get_current_metadata
        
        print("Starting vectorstore rebuild...")
        vectorstore = rebuild_vectorstore_if_needed()
        
        if vectorstore:
            # Save metadata
            current_metadata = get_current_metadata()
            save_metadata(current_metadata)
            
            total_docs = vectorstore._collection.count()
            print(f"✅ Vectorstore rebuilt successfully!")
            print(f"Total documents: {total_docs}")
            print(f"Timestamp: {datetime.now().isoformat()}")
        else:
            print("❌ Failed to rebuild vectorstore")
            
    except Exception as e:
        print(f"❌ Error rebuilding vectorstore: {e}")

def clear_vectorstore():
    """Clear existing vectorstore."""
    from config import CHROMA_DB_PATH
    import shutil
    
    print("=" * 60)
    print("CLEAR VECTORSTORE")
    print("=" * 60)
    
    if not os.path.exists(CHROMA_DB_PATH):
        print("No vectorstore found to clear.")
        return
    
    response = input("Are you sure you want to clear the vectorstore? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("Clear cancelled.")
        return
    
    try:
        shutil.rmtree(CHROMA_DB_PATH)
        print("✅ Vectorstore cleared successfully!")
    except Exception as e:
        print(f"❌ Error clearing vectorstore: {e}")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python manage_vectorstore.py [status|rebuild|clear]")
        print("  status  - Check current vectorstore status")
        print("  rebuild - Manually rebuild vectorstore (costs $16-20)")
        print("  clear   - Clear existing vectorstore")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        check_status()
    elif command == "rebuild":
        rebuild_vectorstore()
    elif command == "clear":
        clear_vectorstore()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python manage_vectorstore.py [status|rebuild|clear]")

if __name__ == "__main__":
    main()
