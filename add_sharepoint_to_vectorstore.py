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
    
    # Load existing MongoDB vectorstore
    print("[*] Loading existing MongoDB vectorstore...")
    from app.mongodb_vectorstore import MongoDBVectorStore
    from config import MONGODB_VECTORSTORE_COLLECTION
    
    embeddings = OpenAIEmbeddings()
    vectorstore = MongoDBVectorStore(
        collection_name=MONGODB_VECTORSTORE_COLLECTION,
        embedding_function=embeddings
    )
    
    # Count existing SharePoint documents
    from pymongo import MongoClient
    from config import MONGODB_URL, MONGODB_DATABASE
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    collection = db[MONGODB_VECTORSTORE_COLLECTION]
    
    current_count = collection.count_documents({})
    sharepoint_count = collection.count_documents({"metadata.source": "cloudfuze_doc360"})
    print(f"[OK] Current vectorstore has {current_count} documents")
    print(f"[OK] Current SharePoint documents: {sharepoint_count}")
    
    # Delete old SharePoint documents (they're bad quality)
    if sharepoint_count > 0:
        print(f"\n[*] Deleting {sharepoint_count} old SharePoint documents...")
        result = collection.delete_many({"metadata.source": "cloudfuze_doc360"})
        print(f"[OK] Deleted {result.deleted_count} documents")
    
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
        
        # Count documents after addition
        new_count = collection.count_documents({})
        new_sharepoint_count = collection.count_documents({"metadata.source": "cloudfuze_doc360"})
        
        print(f"[OK] Successfully added {len(sharepoint_docs)} SharePoint documents")
        print(f"[OK] Vectorstore now has {new_count} total documents")
        print(f"[OK] SharePoint documents: {new_sharepoint_count}")
        
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
        print(f"✅ Added {len(sharepoint_docs)} SharePoint documents to MongoDB Atlas")
        print(f"✅ Total documents in vectorstore: {new_count}")
        print(f"✅ SharePoint documents: {new_sharepoint_count}")
        print("\n🚀 Your chatbot now has SharePoint knowledge!")
        print("   No need to redeploy - MongoDB Atlas is live!")
        
    except Exception as e:
        print(f"[ERROR] Failed to add documents: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_sharepoint_documents()

