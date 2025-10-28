# -*- coding: utf-8 -*-
"""
Test SharePoint Web Scraping
"""

from dotenv import load_dotenv
import os

load_dotenv()

def test_sharepoint_scraping():
    """Test SharePoint web scraping."""
    print("=" * 60)
    print("SHAREPOINT WEB SCRAPING TEST")
    print("=" * 60)
    
    try:
        from app.sharepoint_scraper import SharePointWebScraper
        
        # Create scraper
        scraper = SharePointWebScraper()
        
        # Test scraping a single page
        start_url = f"https://cloudfuzecom.sharepoint.com/sites/DOC360/SitePages/Multi%20User%20Golden%20Image%20Combinations.aspx"
        
        print(f"\n[*] Testing single page scrape: {start_url}")
        
        # Scrape the page
        page_data = scraper.scrape_page(start_url)
        
        if page_data:
            print(f"✅ Page scraped successfully!")
            print(f"   Title: {page_data['title']}")
            
            # Extract content
            documents = scraper.extract_content(page_data)
            
            print(f"\n✅ Extracted {len(documents)} documents")
            
            # Show document types
            faq_count = sum(1 for d in documents if d.metadata.get('content_type') == 'faq')
            table_count = sum(1 for d in documents if d.metadata.get('content_type') == 'table')
            text_count = sum(1 for d in documents if d.metadata.get('content_type') == 'text')
            
            print(f"   FAQs: {faq_count}")
            print(f"   Tables: {table_count}")
            print(f"   Text blocks: {text_count}")
            
            # Show first few documents
            print(f"\n📄 Sample documents:")
            for i, doc in enumerate(documents[:3], 1):
                print(f"\n   Document {i}:")
                print(f"      Type: {doc.metadata.get('content_type')}")
                print(f"      Length: {len(doc.page_content)} chars")
                print(f"      Preview: {doc.page_content[:100]}...")
            
            return documents
        else:
            print("❌ Failed to scrape page")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("🧪 SharePoint Web Scraping Test")
    print()
    docs = test_sharepoint_scraping()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. If scraping works, you can enable it in the vectorstore")
    print("2. Set ENABLE_SHAREPOINT_SOURCE=true in .env")
    print("3. Set INITIALIZE_VECTORSTORE=true to rebuild vectorstore")
    print("4. Run python server.py to start the application")
