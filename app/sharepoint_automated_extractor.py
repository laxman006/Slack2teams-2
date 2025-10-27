# -*- coding: utf-8 -*-
"""
Automated SharePoint Content Extractor

Uses the SharePoint Sites API v1.0 to get page content.
This is the correct, documented approach for accessing SharePoint pages.
"""

import os
import requests
from typing import List, Optional, Set, Dict
from bs4 import BeautifulSoup

from app.sharepoint_auth import sharepoint_auth
from langchain_core.documents import Document

class SharePointAutomatedExtractor:
    """Automated SharePoint content extraction using Sites API."""
    
    def __init__(self):
        self.site_url = os.getenv("SHAREPOINT_SITE_URL", "https://cloudfuzecom.sharepoint.com/sites/DOC360")
        self.crawled_urls: Set[str] = set()
        
        print(f"[*] SharePoint Automated Extractor initialized")
        print(f"   Site: {self.site_url}")
    
    def get_page_content_via_sites_api(self, site_id: str, page_id: str) -> Optional[str]:
        """Get page content using SharePoint Sites API."""
        try:
            headers = sharepoint_auth.get_headers()
            
            # Get page metadata first
            content_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}"
            
            print(f"[*] Getting page metadata...")
            response = requests.get(content_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"   ❌ Failed: {response.status_code}")
                return None
            
            page_data = response.json()
            title = page_data.get('title', 'Untitled')
            
            # Now try to get the canvas content using a different endpoint
            # The correct endpoint for canvas content is:
            try:
                canvas_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}/microsoft.graph.sitepage"
                
                # Get webParts which contain the actual content
                webparts_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}/webParts"
                print(f"[*] Trying to get webParts...")
                
                webparts_response = requests.get(webparts_url, headers=headers, timeout=30)
                
                if webparts_response.status_code == 200:
                    webparts_data = webparts_response.json()
                    webparts = webparts_data.get('value', [])
                    
                    print(f"   ✅ Got {len(webparts)} web parts")
                    
                    # Extract content from web parts
                    all_content = [title]  # Start with title
                    
                    for webpart in webparts:
                        webpart_data = webpart.get('innerHtml', '')
                        if webpart_data:
                            all_content.append(webpart_data)
                    
                    if len(all_content) > 1:
                        html_content = '\n\n'.join(all_content)
                        print(f"   ✅ Extracted content from web parts ({len(html_content)} bytes)")
                        return html_content
                    else:
                        print(f"   ⚠️  No content in web parts")
                else:
                    print(f"   ⚠️  WebParts request failed: {webparts_response.status_code}")
                    
            except Exception as e:
                print(f"   ⚠️  WebParts method failed: {e}")
            
            # Fallback: Return at least the title
            return f"<h1>{title}</h1>"
                
        except Exception as e:
            print(f"[ERROR] Failed to get page content: {e}")
            return None
    
    def get_all_pages_info(self) -> List[Dict]:
        """Get all pages from the site with full info."""
        try:
            headers = sharepoint_auth.get_headers()
            
            from urllib.parse import urlparse
            parsed = urlparse(self.site_url)
            hostname = parsed.netloc
            site_path = parsed.path
            
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
            
            print(f"[*] Getting site info...")
            response = requests.get(graph_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            site_data = response.json()
            site_id = site_data.get('id')
            print(f"   ✅ Site: {site_data.get('name')}")
            
            # Get all pages
            pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages"
            print(f"[*] Getting all pages...")
            pages_response = requests.get(pages_url, headers=headers, timeout=30)
            pages_response.raise_for_status()
            
            pages_data = pages_response.json()
            pages = pages_data.get('value', [])
            print(f"   ✅ Found {len(pages)} pages")
            
            return pages, site_id
            
        except Exception as e:
            print(f"[ERROR] Failed to get pages: {e}")
            return [], None
    
    def extract_content_from_html(self, html_content: str, page_title: str) -> Optional[Document]:
        """Extract structured content from HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get all text content
            text_content = soup.get_text(separator='\n', strip=True)
            
            if not text_content or len(text_content.strip()) < 10:
                return None
            
            # Create document
            doc = Document(
                page_content=text_content[:15000],  # Limit to 15KB
                metadata={
                    "source_type": "sharepoint",
                    "source": "cloudfuze_doc360",
                    "content_type": "sharepoint_page"
                }
            )
            
            return doc
            
        except Exception as e:
            print(f"[ERROR] Failed to extract content: {e}")
            return None
    
    def extract_all(self) -> List[Document]:
        """Extract content from all SharePoint pages."""
        print("=" * 60)
        print("SHAREPOINT AUTOMATED CONTENT EXTRACTION")
        print("=" * 60)
        
        all_documents = []
        
        # Get all pages
        pages, site_id = self.get_all_pages_info()
        
        if not pages or not site_id:
            print("❌ Could not get pages")
            return []
        
        # Process each page
        print(f"\n[*] Extracting content from {len(pages)} pages...\n")
        
        for i, page in enumerate(pages, 1):
            page_title = page.get('title', 'Untitled')
            page_id = page.get('id')
            
            print(f"[{i}/{len(pages)}] {page_title} (ID: {page_id[:30]}...)")
            
            # Get page content using Sites API
            html_content = self.get_page_content_via_sites_api(site_id, page_id)
            
            if html_content:
                # Extract and create document
                doc = self.extract_content_from_html(html_content, page_title)
                
                if doc:
                    doc.metadata['page_title'] = page_title
                    doc.metadata['page_url'] = page.get('webUrl', '')
                    doc.metadata['page_id'] = page_id
                    all_documents.append(doc)
                    print(f"   ✅ Created document ({len(doc.page_content)} chars)")
                else:
                    print(f"   ⚠️  Could not create document from HTML")
            else:
                print(f"   ⚠️  No content extracted")
        
        print(f"\n✅ Extraction complete!")
        print(f"   Documents created: {len(all_documents)}")
        
        return all_documents


def extract_sharepoint_pages() -> List[Document]:
    """Main function for automated extraction."""
    extractor = SharePointAutomatedExtractor()
    return extractor.extract_all()

if __name__ == "__main__":
    docs = extract_sharepoint_pages()
    print(f"\n📄 Total documents: {len(docs)}")
    
    for doc in docs:
        print(f"\n   - {doc.metadata.get('page_title')}: {len(doc.page_content)} chars")

