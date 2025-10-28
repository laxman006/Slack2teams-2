# -*- coding: utf-8 -*-
"""
SharePoint Graph API Content Extractor

Uses Microsoft Graph API to extract SharePoint page content.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from app.sharepoint_auth import sharepoint_auth
from app.sharepoint_models import SharePointMetadata
from langchain_core.documents import Document

def extract_sharepoint_pages() -> List[Document]:
    """Extract content from all SharePoint pages using Microsoft Graph API."""
    print("=" * 60)
    print("SHAREPOINT CONTENT EXTRACTION - MICROSOFT GRAPH API")
    print("=" * 60)
    
    try:
        # Get site info
        site_url = os.getenv("SHAREPOINT_SITE_URL")
        parsed = urlparse(site_url)
        hostname = parsed.netloc
        site_path = parsed.path
        
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
        
        headers = sharepoint_auth.get_headers()
        
        print(f"[*] Getting site info...")
        response = requests.get(graph_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        site_data = response.json()
        site_id = site_data.get('id')
        print(f"✅ Site found: {site_data.get('name')}")
        
        # Get all pages (no filter for now)
        pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages"
        print(f"[*] Getting all pages...")
        
        pages_response = requests.get(pages_url, headers=headers, timeout=30)
        pages_response.raise_for_status()
        
        pages_data = pages_response.json()
        pages = pages_data.get('value', [])
        print(f"✅ Found {len(pages)} pages!")
        
        # Extract content from each page
        all_documents = []
        
        for i, page in enumerate(pages, 1):
            try:
                print(f"\n[{i}/{len(pages)}] Processing: {page.get('title')}")
                
                page_id = page.get('id')
                page_title = page.get('title')
                page_url = page.get('webUrl')
                
                # Get page content
                content_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}"
                content_response = requests.get(content_url, headers=headers, timeout=30)
                
                if content_response.status_code == 200:
                    content_data = content_response.json()
                    
                    # Method 1: Try to get HTML content directly
                    page_text = content_data.get('title', '') + '\n\n'
                    
                    # Get the page in HTML format
                    try:
                        html_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}/content"
                        html_response = requests.get(html_url, headers=headers, timeout=30)
                        
                        if html_response.status_code == 200:
                            html_content = html_response.text
                            
                            if html_content:
                                # Parse HTML to extract text
                                soup = BeautifulSoup(html_content, 'html.parser')
                                text_content = soup.get_text()
                                page_text += text_content
                                print(f"   ✅ Got HTML content ({len(html_content)} bytes)")
                            else:
                                print(f"   ⚠️  Empty HTML content")
                        else:
                            print(f"   ⚠️  HTML content request failed: {html_response.status_code}")
                            
                    except Exception as e:
                        print(f"   ⚠️  HTML content error: {e}")
                    
                    # Create document
                    doc = Document(
                        page_content=page_text[:5000],  # Limit content
                        metadata={
                            "source_type": "sharepoint",
                            "source": "cloudfuze_doc360",
                            "page_url": page_url,
                            "page_title": page_title,
                            "content_type": "page"
                        }
                    )
                    
                    all_documents.append(doc)
                    print(f"   ✅ Extracted {len(page_text)} characters")
                    
                else:
                    print(f"   ⚠️  Skipped: HTTP {content_response.status_code}")
                    
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                continue
        
        print(f"\n✅ Extraction complete!")
        print(f"   Total documents: {len(all_documents)}")
        
        return all_documents
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    docs = extract_sharepoint_pages()
    print(f"\n📄 Total documents: {len(docs)}")

