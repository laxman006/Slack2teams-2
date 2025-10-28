# -*- coding: utf-8 -*-
"""
SharePoint REST API Content Extractor

Uses SharePoint REST API directly to extract page content.
Works with existing access token from Microsoft Graph.
"""

import os
import requests
from typing import List, Optional, Set, Dict
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup

from app.sharepoint_auth import sharepoint_auth
from langchain_core.documents import Document

class SharePointRESTExtractor:
    """Extract SharePoint page content using REST API."""
    
    def __init__(self):
        self.site_url = os.getenv("SHAREPOINT_SITE_URL", "https://cloudfuzecom.sharepoint.com/sites/DOC360")
        self.crawled_urls: Set[str] = set()
        
        print(f"[*] SharePoint REST Extractor initialized")
        print(f"   Site: {self.site_url}")
    
    def get_page_html(self, page_url: str) -> Optional[str]:
        """Get SharePoint page HTML content using REST API."""
        try:
            # Parse the page URL to get the server-relative URL
            parsed = urlparse(page_url)
            site_base = f"{parsed.scheme}://{parsed.netloc}"
            path_parts = parsed.path.split('/')
            
            # Find the site name and build server-relative path
            sites_index = -1
            for i, part in enumerate(path_parts):
                if part == 'sites':
                    sites_index = i
                    break
            
            if sites_index == -1:
                print(f"[ERROR] Could not parse site name from URL: {page_url}")
                return None
            
            # Build server-relative URL
            server_relative_path = '/' + '/'.join(path_parts[sites_index:])
            
            # SharePoint REST API endpoint
            rest_url = f"{site_base}{server_relative_path}"
            
            # For SharePoint REST API, we can't use Graph API token directly
            # SharePoint pages require browser-based access or different authentication
            # For now, let's try without authentication to see what happens
            
            print(f"[*] Getting page content from REST API...")
            print(f"   URL: {rest_url}")
            print(f"   ⚠️  Note: SharePoint pages require special authentication")
            
            # Try accessing the page without auth first to see what we get
            headers = {'Accept': 'text/html,application/xhtml+xml'}
            response = requests.get(rest_url, headers=headers, allow_redirects=True, timeout=30)
            
            if response.status_code == 200:
                html_content = response.text
                print(f"   ✅ Got HTML content ({len(html_content)} bytes)")
                return html_content
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Failed to get page HTML: {e}")
            return None
    
    def extract_content_from_html(self, html_content: str, page_url: str, page_title: str) -> List[Document]:
        """Extract content from HTML and convert to Documents."""
        documents = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract all text content
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Clean up text
            lines = [line.strip() for line in text_content.splitlines() if line.strip()]
            cleaned_text = '\n'.join(lines)
            
            if cleaned_text:
                doc = Document(
                    page_content=cleaned_text[:10000],  # Limit to 10KB
                    metadata={
                        "source_type": "sharepoint",
                        "source": "cloudfuze_doc360",
                        "page_url": page_url,
                        "page_title": page_title,
                        "content_type": "page"
                    }
                )
                documents.append(doc)
                print(f"   ✅ Extracted {len(cleaned_text)} characters")
            
            return documents
            
        except Exception as e:
            print(f"[ERROR] Failed to extract content: {e}")
            return []
    
    def get_all_pages_from_graph(self) -> List[Dict]:
        """Get list of pages from Microsoft Graph API."""
        try:
            headers = sharepoint_auth.get_headers()
            
            # Get site info
            parsed = urlparse(self.site_url)
            hostname = parsed.netloc
            site_path = parsed.path
            
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
            
            print(f"[*] Getting site info from Graph API...")
            response = requests.get(graph_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            site_data = response.json()
            site_id = site_data.get('id')
            print(f"   ✅ Site: {site_data.get('name')}")
            
            # Get pages
            pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages"
            print(f"[*] Getting pages list from Graph API...")
            pages_response = requests.get(pages_url, headers=headers, timeout=30)
            pages_response.raise_for_status()
            
            pages_data = pages_response.json()
            pages = pages_data.get('value', [])
            print(f"   ✅ Found {len(pages)} pages")
            
            return pages
            
        except Exception as e:
            print(f"[ERROR] Failed to get pages list: {e}")
            return []
    
    def extract_all_pages(self) -> List[Document]:
        """Extract content from all SharePoint pages."""
        print("=" * 60)
        print("SHAREPOINT CONTENT EXTRACTION - REST API")
        print("=" * 60)
        
        all_documents = []
        
        try:
            # Get list of pages from Graph API
            pages = self.get_all_pages_from_graph()
            
            if not pages:
                print("❌ No pages found")
                return []
            
            # Process each page
            print(f"\n[*] Extracting content from {len(pages)} pages...\n")
            
            for i, page in enumerate(pages, 1):
                page_title = page.get('title', 'Untitled')
                page_url = page.get('webUrl')
                
                print(f"[{i}/{len(pages)}] {page_title}")
                
                if page_url in self.crawled_urls:
                    print(f"   ⏭️  Already processed")
                    continue
                
                # Get HTML content using REST API
                html_content = self.get_page_html(page_url)
                
                if html_content:
                    # Extract and create document
                    page_docs = self.extract_content_from_html(html_content, page_url, page_title)
                    all_documents.extend(page_docs)
                    self.crawled_urls.add(page_url)
                else:
                    print(f"   ⚠️  Could not get content")
            
            print(f"\n✅ Extraction complete!")
            print(f"   Pages processed: {len(self.crawled_urls)}")
            print(f"   Documents created: {len(all_documents)}")
            
            return all_documents
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []


def extract_sharepoint_pages() -> List[Document]:
    """Main function to extract SharePoint pages using REST API."""
    extractor = SharePointRESTExtractor()
    return extractor.extract_all_pages()

if __name__ == "__main__":
    docs = extract_sharepoint_pages()
    print(f"\n📄 Total documents: {len(docs)}")

