"""
Check the quality and content of specific SharePoint pages in MongoDB
"""
from pymongo import MongoClient
from config import MONGODB_URL, MONGODB_DATABASE, MONGODB_VECTORSTORE_COLLECTION
from dotenv import load_dotenv

load_dotenv()

def check_sharepoint_pages():
    """Check specific SharePoint pages in MongoDB."""
    
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    collection = db[MONGODB_VECTORSTORE_COLLECTION]
    
    print("\n" + "="*80)
    print("CHECKING SHAREPOINT PAGE CONTENT QUALITY")
    print("="*80 + "\n")
    
    # Find all SharePoint documents
    sharepoint_docs = list(collection.find({
        "metadata.source": "cloudfuze_doc360"
    }))
    
    print(f"Total SharePoint documents: {len(sharepoint_docs)}\n")
    
    # Look for specific pages
    target_pages = [
        "Multi User Golden Image Combinations",
        "Slack to Teams",
        "Message Migration",
        "Box"
    ]
    
    for target in target_pages:
        print(f"\n{'='*80}")
        print(f"Searching for: {target}")
        print(f"{'='*80}")
        
        found = False
        for doc in sharepoint_docs:
            content = doc.get('text', '')
            metadata = doc.get('metadata', {})
            page_title = metadata.get('page_title', '')
            page_url = metadata.get('page_url', '')
            
            # Check if target is in title or content
            if target.lower() in page_title.lower() or target.lower() in content.lower()[:500]:
                found = True
                print(f"\n✓ FOUND!")
                print(f"  Page Title: {page_title}")
                print(f"  Page URL: {page_url}")
                print(f"  Content Length: {len(content)} characters")
                print(f"\n  Content Preview (first 800 chars):")
                print(f"  {'-'*76}")
                print(f"  {content[:800]}")
                print(f"  {'-'*76}")
                
                # Check if it has meaningful content
                if len(content) < 200:
                    print("\n  ⚠️  WARNING: Content is very short!")
                
                # Check for key terms
                key_terms = ['migration', 'features', 'supported', 'combination', 'source', 'destination']
                found_terms = [term for term in key_terms if term.lower() in content.lower()]
                print(f"\n  Key terms found: {', '.join(found_terms) if found_terms else 'None'}")
                
                break
        
        if not found:
            print(f"\n✗ NOT FOUND in any SharePoint document")
    
    # Summary of all pages
    print(f"\n\n{'='*80}")
    print("ALL SHAREPOINT PAGES SUMMARY")
    print(f"{'='*80}\n")
    
    for i, doc in enumerate(sharepoint_docs, 1):
        metadata = doc.get('metadata', {})
        content = doc.get('text', '')
        page_title = metadata.get('page_title', 'Unknown')
        content_length = len(content)
        
        # Show first 50 chars of content
        content_preview = content[:50].replace('\n', ' ')
        
        print(f"{i:2d}. {page_title}")
        print(f"    Length: {content_length} chars | Preview: {content_preview}...")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    check_sharepoint_pages()


