# -*- coding: utf-8 -*-
"""
Test Full SharePoint Content Extraction
"""

from dotenv import load_dotenv
load_dotenv()

def test_full_extraction():
    """Test full SharePoint content extraction."""
    print("=" * 60)
    print("TESTING FULL SHAREPOINT CONTENT EXTRACTION")
    print("=" * 60)
    
    try:
        from app.sharepoint_rest_extractor import extract_sharepoint_pages
        
        print("[*] Extracting content from SharePoint using REST API...\n")
        
        documents = extract_sharepoint_pages()
        
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"✅ Extracted {len(documents)} documents\n")
        
        for i, doc in enumerate(documents, 1):
            print(f"Document {i}:")
            print(f"   Title: {doc.metadata.get('page_title')}")
            print(f"   URL: {doc.metadata.get('page_url')}")
            print(f"   Content length: {len(doc.page_content)} characters")
            print(f"   Preview: {doc.page_content[:150]}...")
            print()
        
        return documents
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    docs = test_full_extraction()
    
    if docs:
        print("✅ Ready to add to vectorstore!")
        print("\nNext steps:")
        print("1. Set ENABLE_SHAREPOINT_SOURCE=true")
        print("2. Set INITIALIZE_VECTORSTORE=true")
        print("3. Run: python server.py")
    else:
        print("❌ No documents extracted")
