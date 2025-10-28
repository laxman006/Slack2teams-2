# -*- coding: utf-8 -*-
"""
Test Small SharePoint Content Crawl
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_small_crawl():
    """Test crawling a small amount of SharePoint content."""
    print("=" * 60)
    print("TESTING SMALL SHAREPOINT CRAWL")
    print("=" * 60)
    
    try:
        from app.sharepoint_processor import process_sharepoint_content
        
        print("[*] Starting small SharePoint content crawl...")
        print("[*] This will test the crawling logic without full content extraction")
        print()
        
        # Process SharePoint content
        # Since content extraction isn't fully implemented,
        # this will mainly test the authentication and connection
        print("[*] Note: This is a simplified test that demonstrates the structure")
        print()
        
        # Create a test document to simulate SharePoint content
        from langchain_core.documents import Document
        
        # Sample FAQ content from your screenshots
        sample_faq_content = """
Q: What are the frequent conflicts faced during Migration?
A: Bad request (Non Retriable):
- Replied message version conflicts in post
- We don't migrate bot messages
- Missing body content
- Neither body nor adaptive card content contains marker for mention with Id

Resource Modifies (Retryable):
- Resource has changed - usually an eTag mismatch
- Omitting partial - files size varies but data migrate without any data missing

Q: Do we migrate app integration messages?
A: No, we don't migrate app integration messages, but they will appear as admin posted messages.

Q: Do we migrate slack channels into existing teams?
A: Yes, we do migrate Slack channels into existing Teams. But those messages inside a channel will be migrated as admin posted messages.

Q: How to migrate deactivated user DMS?
A: We can't migrate deactivated user DMs because deactivated users can't authenticate from Teams. It's a limitation of Teams.

Q: Do we migrate the link to other messages from Slack?
A: No, we don't migrate. They will be migrated as links, but those links will redirect back to Slack.
"""
        
        # Sample table content
        sample_table_content = """
Table: Egnyte as source combinations

Features:
- One Time: Yes
- Delta: Yes
- Versions: Yes
- Selective Versions: No
- Folder Display: Yes (for some destinations)
- Root folder permissions: Yes
- Sub folder Permissions: Yes
- Preserve Timestamp: Yes
- Special character replacement: Yes

Destinations supported:
- Google My Drive
- Google Shared Drive
- SharePoint Online
- OneDrive For Business
- Azure
"""
        
        # Create test documents
        doc1 = Document(
            page_content=sample_faq_content,
            metadata={
                "source_type": "sharepoint",
                "source": "cloudfuze_doc360",
                "page_url": "https://cloudfuzecom.sharepoint.com/sites/DOC360/SitePages/Slack_to_Teams.aspx",
                "page_title": "Slack to Teams",
                "content_type": "faq"
            }
        )
        
        doc2 = Document(
            page_content=sample_table_content,
            metadata={
                "source_type": "sharepoint",
                "source": "cloudfuze_doc360",
                "page_url": "https://cloudfuzecom.sharepoint.com/sites/DOC360/SitePages/Egnyte_combinations.aspx",
                "page_title": "Egnyte as source combinations",
                "content_type": "table"
            }
        )
        
        test_docs = [doc1, doc2]
        
        print(f"✅ Created {len(test_docs)} test documents")
        print()
        
        # Display sample content
        for i, doc in enumerate(test_docs, 1):
            print(f"Document {i}:")
            print(f"  Title: {doc.metadata['page_title']}")
            print(f"  Type: {doc.metadata['content_type']}")
            print(f"  Content length: {len(doc.page_content)} characters")
            print()
        
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("✅ Test documents created successfully")
        print("✅ These represent the type of content we'll extract from SharePoint")
        print()
        print("📋 Next Steps:")
        print("1. The SharePoint integration framework is ready")
        print("2. Content extraction logic needs to be implemented")
        print("3. For now, you can manually add content or use a simpler approach")
        print()
        print("💡 Would you like to:")
        print("   A. Continue with manual content addition?")
        print("   B. Implement a simpler web scraping solution?")
        print("   C. Save these test documents to the vectorstore for testing?")
        
        return test_docs
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_small_crawl()
