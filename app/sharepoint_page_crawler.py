# -*- coding: utf-8 -*-
"""
SharePoint Page Crawler using Graph API

Crawls SharePoint pages using Microsoft Graph API to extract page content.
Follows links recursively and extracts text, tables, and structured content.
Much faster and more reliable than Selenium-based extraction.
"""

import os
import re
import requests
import hashlib
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlparse, urljoin, unquote
from datetime import datetime
from langchain_core.documents import Document


class SharePointPageCrawler:
    """Crawls SharePoint pages using Microsoft Graph API."""
    
    def __init__(
        self, 
        site_url: str, 
        auth_headers: Dict[str, str],
        start_page: str = None,
        max_depth: int = 3
    ):
        """
        Initialize SharePoint page crawler.
        
        Args:
            site_url: SharePoint site URL
            auth_headers: Authentication headers with Bearer token
            start_page: Starting page path (e.g., /SitePages/Page.aspx)
            max_depth: Maximum depth for recursive crawling
        """
        self.site_url = site_url
        self.auth_headers = auth_headers
        self.start_page = start_page
        self.max_depth = max_depth
        
        # Parse site URL
        parsed_url = urlparse(site_url)
        self.hostname = parsed_url.netloc
        self.site_path = parsed_url.path
        
        # Track visited pages
        self.visited_pages: Set[str] = set()
        self.page_documents: List[Document] = []
        
        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'pages_skipped': 0,
            'links_found': 0,
            'errors': []
        }
        
        print(f"[*] SharePoint Page Crawler initialized")
        print(f"    Site: {site_url}")
        print(f"    Start page: {start_page}")
        print(f"    Max depth: {max_depth}")
    
    def _get_site_id(self) -> Optional[str]:
        """Get SharePoint site ID using Graph API."""
        try:
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{self.hostname}:{self.site_path}"
            
            response = requests.get(graph_url, headers=self.auth_headers, timeout=30)
            response.raise_for_status()
            
            site_data = response.json()
            site_id = site_data.get('id')
            
            print(f"[OK] Got site ID: {site_id}")
            return site_id
            
        except Exception as e:
            print(f"[ERROR] Failed to get site ID: {e}")
            return None
    
    def _list_all_pages(self, site_id: str) -> List[Dict[str, Any]]:
        """List all pages in the site."""
        try:
            pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages"
            
            all_pages = []
            
            # Handle pagination
            while pages_url:
                response = requests.get(pages_url, headers=self.auth_headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                pages = data.get('value', [])
                all_pages.extend(pages)
                
                # Check for next page
                pages_url = data.get('@odata.nextLink')
            
            print(f"[OK] Found {len(all_pages)} total pages in site")
            return all_pages
            
        except Exception as e:
            print(f"[ERROR] Failed to list pages: {e}")
            return []
    
    def _find_page_by_path(self, pages: List[Dict[str, Any]], page_path: str) -> Optional[Dict[str, Any]]:
        """Find a specific page by its path."""
        # Normalize and decode the page path
        page_path = page_path.strip('/')
        page_path_decoded = unquote(page_path)
        
        # Extract just the filename
        page_filename = page_path_decoded.split('/')[-1]
        page_filename_noext = page_filename.replace('.aspx', '').lower()
        
        print(f"[DEBUG] Looking for page: {page_path_decoded}")
        print(f"[DEBUG] Filename: {page_filename}")
        
        for page in pages:
            web_url = page.get('webUrl', '')
            name = page.get('name', '')
            title = page.get('title', '')
            
            # Decode the web URL for comparison
            web_url_decoded = unquote(web_url)
            
            # Strategy 1: Match full path in URL
            if page_path_decoded.lower() in web_url_decoded.lower():
                print(f"[DEBUG] ✓ Matched by full path: {name}")
                return page
            
            # Strategy 2: Match by exact filename
            if name and page_filename.lower() == name.lower():
                print(f"[DEBUG] ✓ Matched by filename: {name}")
                return page
            
            # Strategy 3: Match by filename without extension
            if name:
                name_noext = name.replace('.aspx', '').lower()
                if page_filename_noext == name_noext:
                    print(f"[DEBUG] ✓ Matched by filename (no ext): {name}")
                    return page
            
            # Strategy 4: Fuzzy match on title (for user-friendly URLs)
            if title:
                title_normalized = title.lower().replace(' ', '')
                filename_normalized = page_filename_noext.replace(' ', '').replace('_', '')
                if title_normalized in filename_normalized or filename_normalized in title_normalized:
                    print(f"[DEBUG] ✓ Matched by title: {title}")
                    return page
        
        # If no match found, print available pages for debugging
        print(f"\n[DEBUG] ❌ Could not find page. Available pages in site:")
        for i, page in enumerate(pages, 1):
            print(f"  {i}. Name: {page.get('name')}")
            print(f"     Title: {page.get('title')}")
            print(f"     URL: {unquote(page.get('webUrl', ''))}")
            print()
        
        return None
    
    def _get_page_content(self, site_id: str, page_id: str) -> Optional[Dict[str, Any]]:
        """Get page content including webParts."""
        try:
            # Get page with content
            page_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}"
            
            response = requests.get(
                page_url,
                headers=self.auth_headers,
                params={'$expand': 'canvasLayout'},
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"[ERROR] Failed to get page content: {e}")
            return None
    
    def _extract_links_from_page(self, page_data: Dict[str, Any]) -> List[str]:
        """Extract links from page content."""
        links = []
        
        try:
            # Extract from canvasLayout (webParts)
            canvas_layout = page_data.get('canvasLayout', {})
            
            # Horizontal sections
            horizontal_sections = canvas_layout.get('horizontalSections', [])
            for section in horizontal_sections:
                columns = section.get('columns', [])
                for column in columns:
                    webparts = column.get('webparts', [])
                    for webpart in webparts:
                        # Extract links from webpart content
                        inner_html = webpart.get('innerHtml', '')
                        
                        # Find href attributes
                        href_pattern = r'href=["\']([^"\']+)["\']'
                        matches = re.findall(href_pattern, inner_html)
                        links.extend(matches)
            
            # Vertical sections
            vertical_section = canvas_layout.get('verticalSection', {})
            if vertical_section:
                webparts = vertical_section.get('webparts', [])
                for webpart in webparts:
                    inner_html = webpart.get('innerHtml', '')
                    href_pattern = r'href=["\']([^"\']+)["\']'
                    matches = re.findall(href_pattern, inner_html)
                    links.extend(matches)
            
            # Filter to SharePoint pages only
            sharepoint_links = []
            for link in links:
                # Decode URL-encoded links
                link = unquote(link)
                
                # Check if it's a SharePoint page
                if 'SitePages' in link and (link.endswith('.aspx') or 'aspx' in link):
                    # Make absolute if relative
                    if not link.startswith('http'):
                        link = urljoin(self.site_url, link)
                    
                    # Only include links from the same site
                    if self.hostname in link:
                        sharepoint_links.append(link)
            
            # Remove duplicates
            sharepoint_links = list(set(sharepoint_links))
            
            self.stats['links_found'] += len(sharepoint_links)
            
            return sharepoint_links
            
        except Exception as e:
            print(f"[WARNING] Failed to extract links: {e}")
            return []
    
    def _create_document_from_page(
        self, 
        page_data: Dict[str, Any],
        page_content_text: str
    ) -> Optional[Document]:
        """Create a LangChain Document from page data."""
        try:
            # Extract metadata
            page_title = page_data.get('title', 'Untitled')
            page_url = page_data.get('webUrl', '')
            page_id = page_data.get('id', '')
            last_modified = page_data.get('lastModifiedDateTime', '')
            created = page_data.get('createdDateTime', '')
            
            # Extract page path from URL
            page_path = ''
            if page_url:
                parsed = urlparse(page_url)
                page_path = parsed.path
            
            # Create metadata
            metadata = {
                'source_type': 'sharepoint_page',
                'source': 'cloudfuze_sharepoint',
                'page_title': page_title,
                'page_url': page_url,
                'page_path': page_path,
                'page_id': page_id,
                'last_modified': last_modified,
                'created': created,
                'content_type': 'html_page',
            }
            
            # Create document
            doc = Document(
                page_content=page_content_text,
                metadata=metadata
            )
            
            return doc
            
        except Exception as e:
            print(f"[ERROR] Failed to create document: {e}")
            return None
    
    def _crawl_page_recursive(
        self, 
        site_id: str,
        all_pages: List[Dict[str, Any]],
        page_url: str,
        depth: int = 0
    ) -> List[Document]:
        """Recursively crawl a page and its linked pages."""
        documents = []
        
        # Check depth limit
        if depth > self.max_depth:
            return documents
        
        # Check if already visited
        if page_url in self.visited_pages:
            self.stats['pages_skipped'] += 1
            return documents
        
        # Mark as visited
        self.visited_pages.add(page_url)
        
        print(f"\n[*] Crawling page (depth {depth}): {page_url}")
        
        try:
            # Extract page path from URL
            parsed_url = urlparse(page_url)
            page_path = parsed_url.path
            
            # Find the page in the list
            page_info = self._find_page_by_path(all_pages, page_path)
            
            if not page_info:
                print(f"[WARNING] Could not find page in site: {page_path}")
                return documents
            
            page_id = page_info.get('id')
            
            # Get page content
            page_data = self._get_page_content(site_id, page_id)
            
            if not page_data:
                print(f"[WARNING] Could not get page content")
                return documents
            
            # Parse page content using the parser
            from app.sharepoint_page_parser import SharePointPageParser
            parser = SharePointPageParser()
            
            page_content_text = parser.parse_page_content(page_data)
            
            if page_content_text and page_content_text.strip():
                # Create document
                doc = self._create_document_from_page(page_data, page_content_text)
                
                if doc:
                    documents.append(doc)
                    self.stats['pages_crawled'] += 1
                    print(f"[OK] Extracted page: {page_data.get('title', 'Untitled')} ({len(page_content_text)} chars)")
            
            # Extract links from page
            links = self._extract_links_from_page(page_data)
            
            if links:
                print(f"[*] Found {len(links)} links on this page")
            
            # Recursively crawl linked pages
            for link in links:
                if link not in self.visited_pages:
                    child_docs = self._crawl_page_recursive(site_id, all_pages, link, depth + 1)
                    documents.extend(child_docs)
            
        except Exception as e:
            error_msg = f"Failed to crawl page {page_url}: {e}"
            print(f"[ERROR] {error_msg}")
            self.stats['errors'].append(error_msg)
        
        return documents
    
    def crawl(self) -> List[Document]:
        """
        Crawl SharePoint pages starting from the configured start page.
        
        Returns:
            List of Document objects containing page content
        """
        print("\n" + "=" * 70)
        print("SHAREPOINT PAGE CRAWLER - STARTING")
        print("=" * 70)
        
        # Get site ID
        site_id = self._get_site_id()
        if not site_id:
            print("[ERROR] Could not get site ID")
            return []
        
        # List all pages in the site
        print("\n[*] Listing all pages in site...")
        all_pages = self._list_all_pages(site_id)
        
        if not all_pages:
            print("[ERROR] No pages found in site")
            return []
        
        # Determine starting page
        if self.start_page:
            start_url = urljoin(self.site_url, self.start_page)
        else:
            # Use first page if no start page specified
            start_url = all_pages[0].get('webUrl', '')
        
        print(f"\n[*] Starting crawl from: {start_url}")
        
        # Crawl pages recursively
        documents = self._crawl_page_recursive(site_id, all_pages, start_url, depth=0)
        
        # Print summary
        print("\n" + "=" * 70)
        print("PAGE CRAWLING COMPLETE")
        print("=" * 70)
        print(f"Pages crawled: {self.stats['pages_crawled']}")
        print(f"Pages skipped: {self.stats['pages_skipped']}")
        print(f"Links found: {self.stats['links_found']}")
        print(f"Documents created: {len(documents)}")
        print(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\nErrors encountered:")
            for error in self.stats['errors'][:5]:
                print(f"  - {error}")
        
        return documents


def get_sharepoint_page_crawler(
    site_url: str = None,
    auth_headers: Dict[str, str] = None,
    start_page: str = None,
    max_depth: int = None
) -> SharePointPageCrawler:
    """
    Get a configured SharePoint page crawler instance.
    
    Args:
        site_url: SharePoint site URL (uses env var if not provided)
        auth_headers: Authentication headers (uses sharepoint_auth if not provided)
        start_page: Starting page path (uses env var if not provided)
        max_depth: Maximum crawl depth (uses env var if not provided)
    """
    if site_url is None:
        site_url = os.getenv('SHAREPOINT_SITE_URL', 'https://cloudfuzecom.sharepoint.com/sites/DOC360')
    
    if auth_headers is None:
        from app.sharepoint_auth import sharepoint_auth
        auth_headers = sharepoint_auth.get_headers()
    
    if start_page is None:
        start_page = os.getenv('SHAREPOINT_START_PAGE', '/SitePages/Home.aspx')
    
    if max_depth is None:
        max_depth = int(os.getenv('SHAREPOINT_MAX_DEPTH', '3'))
    
    return SharePointPageCrawler(site_url, auth_headers, start_page, max_depth)

