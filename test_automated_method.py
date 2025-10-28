# -*- coding: utf-8 -*-
"""
Test the automated SharePoint extraction method
"""

from dotenv import load_dotenv
load_dotenv()

from app.sharepoint_automated_extractor import SharePointAutomatedExtractor

def test_automated_method():
    """Test the automated extraction method."""
    
    print("=" * 60)
    print("TESTING AUTOMATED SHAREPOINT EXTRACTION")
    print("=" * 60)
    
    extractor = SharePointAutomatedExtractor()
    documents = extractor.extract_all()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if documents:
        print(f"✅ Extracted {len(documents)} documents\n")
        
        for doc in documents:
            print(f"   Document:")
            print(f"      Title: {doc.metadata.get('page_title')}")
            print(f"      Length: {len(doc.page_content)} characters")
            print(f"      Preview: {doc.page_content[:200]}...\n")
    else:
        print("❌ No documents extracted")
    
    return documents

if __name__ == "__main__":
    docs = test_automated_method()
    
    if docs:
        print("\n✅ SUCCESS! Ready to add to vectorstore!")
    else:
        print("\n⚠️  No content extracted - API limitations")

