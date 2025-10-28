# -*- coding: utf-8 -*-
"""
Check if SharePoint data is in vectorstore
"""

from app.vectorstore import vectorstore
import json

def check_sharepoint_in_vectorstore():
    """Check if SharePoint documents are in the vectorstore."""
    
    print("=" * 60)
    print("CHECKING SHAREPOINT DATA IN VECTORSTORE")
    print("=" * 60)
    
    if not vectorstore:
        print("❌ Vectorstore not loaded")
        return
    
    # Search for SharePoint-specific content
    test_queries = [
        "Do we migrate app integration messages from Slack to Teams?",
        "What features are supported for Box to OneDrive migration?",
        "Slack to Teams migration",
        "SharePoint combinations",
        "Egnyte source combinations"
    ]
    
    print(f"\n[*] Testing {len(test_queries)} SharePoint-related queries...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query}")
        
        try:
            # Use similarity_search to find relevant documents
            docs = vectorstore.similarity_search(query, k=3)
            
            print(f"   Found {len(docs)} relevant documents:")
            
            for j, doc in enumerate(docs, 1):
                metadata = doc.metadata
                source_type = metadata.get('source_type', 'unknown')
                page_title = metadata.get('page_title', 'Unknown')
                content_preview = doc.page_content[:150] + "..."
                
                print(f"\n   Document {j}:")
                print(f"      Source: {source_type}")
                print(f"      Title: {page_title}")
                print(f"      Preview: {content_preview}")
                
                # Check if it's SharePoint content
                if source_type == 'sharepoint':
                    print(f"      ✅ This is SharePoint content!")
            
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
        
        print()
    
    # Count documents by source type
    print("\n[*] Analyzing document distribution...")
    print("Note: Getting exact counts requires iterating through all documents")
    print("Vectorstore currently has documents loaded.")
    
    # Try to get collection info
    try:
        if hasattr(vectorstore, '_collection'):
            # Try to get count from collection
            try:
                count = vectorstore._collection.count()
                print(f"\nTotal documents in vectorstore: {count}")
            except:
                print("\nCould not get exact count")
    except Exception as e:
        print(f"Could not access collection info: {e}")

if __name__ == "__main__":
    check_sharepoint_in_vectorstore()

