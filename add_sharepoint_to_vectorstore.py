# -*- coding: utf-8 -*-
"""
Add SharePoint documents directly to vectorstore
"""

import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

def add_sharepoint_documents():
    """Add SharePoint documents to vectorstore."""
    
    print("=" * 60)
    print("ADDING SHAREPOINT DOCUMENTS TO VECTORSTORE")
    print("=" * 60)
    
    # Load existing vectorstore
    print("[*] Loading existing vectorstore...")
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(
        persist_directory="data/chroma_db",
        embedding_function=embeddings
    )
    
    current_count = vectorstore._collection.count()
    print(f"[OK] Current vectorstore has {current_count} documents")
    
    # Extract SharePoint documents again
    print("\n[*] Extracting SharePoint documents...")
    from app.sharepoint_processor import process_sharepoint_content
    
    sharepoint_docs = process_sharepoint_content()
    
    if not sharepoint_docs:
        print("[ERROR] No SharePoint documents extracted")
        return
    
    print(f"[OK] Extracted {len(sharepoint_docs)} SharePoint documents")
    
    # Add to vectorstore
    print(f"\n[*] Adding {len(sharepoint_docs)} SharePoint documents to vectorstore...")
    
    try:
        vectorstore.add_documents(sharepoint_docs)
        
        new_count = vectorstore._collection.count()
        added_count = new_count - current_count
        
        print(f"[OK] Successfully added {added_count} documents")
        print(f"[OK] Vectorstore now has {new_count} total documents")
        
        # Update metadata
        print("[*] Updating metadata...")
        from datetime import datetime
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "vectorstore_exists": True,
            "enabled_sources": ["sharepoint"],
            "sharepoint": "https://cloudfuzecom.sharepoint.com/sites/DOC360/SitePages/Multi%20User%20Golden%20Image%20Combinations.aspx"
        }
        
        import json
        with open("data/vectorstore_metadata.json", "w") as f:
            json.dump(metadata, f, indent=4)
        
        print("[OK] Metadata updated")
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"✅ Added {added_count} SharePoint documents to vectorstore")
        print(f"✅ Total documents: {new_count}")
        print("\nYour chatbot now has SharePoint knowledge!")
        
    except Exception as e:
        print(f"[ERROR] Failed to add documents: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_sharepoint_documents()

