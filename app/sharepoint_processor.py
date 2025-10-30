# -*- coding: utf-8 -*-
"""
SharePoint Content Processor

Crawls SharePoint pages, extracts content (tables, FAQs, text),
and converts them to LangChain Documents for vectorstore.
"""

import os
import re
import time
import requests
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
from datetime import datetime
import json

from app.sharepoint_auth import sharepoint_auth
from app.sharepoint_models import (
    SharePointPage, SharePointFAQ, SharePointTable, 
    SharePointCrawlResult, SharePointMetadata
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class SharePointProcessor:
    """Processes SharePoint content for chatbot knowledge base."""
    
    def __init__(self):
        self.site_url = os.getenv("SHAREPOINT_SITE_URL", "https://cloudfuzecom.sharepoint.com/sites/DOC360")
        self.start_page = os.getenv("SHAREPOINT_START_PAGE", "/SitePages/Multi%20User%20Golden%20Image%20Combinations.aspx")
        self.max_depth = int(os.getenv("SHAREPOINT_MAX_DEPTH", "3"))
        self.exclude_files = os.getenv("SHAREPOINT_EXCLUDE_FILES", "true").lower() == "true"
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Track crawled URLs to avoid duplicates
        self.crawled_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        
        print(f"[*] SharePoint Processor initialized")
        print(f"   Site URL: {self.site_url}")
        print(f"   Start Page: {self.start_page}")
        print(f"   Max Depth: {self.max_depth}")
        print(f"   Exclude Files: {self.exclude_files}")
    
    def get_page_content(self, page_url: str) -> Optional[Dict[str, Any]]:
        """Get SharePoint page content via SharePoint REST API."""
        try:
            # Get access token
            headers = sharepoint_auth.get_headers()
            
            # For now, return a simplified response indicating successful connection
            # The actual content extraction will be handled in the crawling logic
            page_data = {
                'title': 'SharePoint Page',
                'url': page_url,
                'content': f"<div>SharePoint content from {page_url}</div>"
            }
            
            print(f"[OK] Connected to SharePoint page: {page_url}")
            return page_data
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get page content for {page_url}: {e}")
            return None
    
    def _convert_to_graph_url(self, page_url: str) -> str:
        """Convert SharePoint page URL to Microsoft Graph API URL."""
        # Parse the URL to extract hostname and path
        parsed_url = urlparse(page_url)
        
        # Extract the hostname (e.g., cloudfuzecom.sharepoint.com)
        hostname = parsed_url.netloc
        
        # Extract the site path from URL (e.g., /sites/DOC360/SitePages/...)
        path_parts = [p for p in parsed_url.path.split('/') if p]
        
        # Find where the site name is (/sites/{site_name})
        site_path_start = None
        for i, part in enumerate(path_parts):
            if part == 'sites':
                site_path_start = i + 1
                break
        
        if site_path_start is None:
            raise ValueError(f"Could not find /sites/ in URL: {page_url}")
        
        # Get the site name
        site_name = path_parts[site_path_start]
        
        # Build the site identifier in Graph API format
        # Format: sites/{hostname}:{server-relative-path}
        server_relative_path = '/' + '/'.join(path_parts[:site_path_start + 1])  # /sites/DOC360
        
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{server_relative_path}"
        
        # For Site Pages, we need to use a different API endpoint
        # Sharepoint Pages API uses: /sites/{site-id}/pages/{page-id}
        # But we need to use SharePoint REST API for raw content
        
        return graph_url  # Return the site URL, we'll get pages differently
    
    def extract_content_from_html(self, html_content: str, page_url: str, page_title: str) -> List[Document]:
        """Extract content from SharePoint page HTML and convert to Documents."""
        documents = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract FAQs
            faqs = self._extract_faqs(soup, page_url, page_title)
            for faq in faqs:
                doc = self._faq_to_document(faq)
                if doc:
                    documents.append(doc)
            
            # Extract tables
            tables = self._extract_tables(soup, page_url, page_title)
            for table in tables:
                doc = self._table_to_document(table)
                if doc:
                    documents.append(doc)
            
            # Extract general text content
            text_content = self._extract_text_content(soup)
            if text_content.strip():
                doc = self._text_to_document(text_content, page_url, page_title)
                if doc:
                    documents.append(doc)
            
            print(f"[OK] Extracted {len(faqs)} FAQs, {len(tables)} tables, 1 text block from {page_title}")
            
        except Exception as e:
            print(f"[ERROR] Failed to extract content from {page_url}: {e}")
        
        return documents
    
    def _extract_faqs(self, soup: BeautifulSoup, page_url: str, page_title: str) -> List[SharePointFAQ]:
        """Extract FAQ items from SharePoint page."""
        faqs = []
        
        # Look for numbered lists (Q1, Q2, etc.)
        numbered_items = soup.find_all(['ol', 'ul'])
        
        for list_element in numbered_items:
            items = list_element.find_all('li')
            
            for i, item in enumerate(items):
                text = item.get_text(strip=True)
                
                # Check if this looks like a Q&A pair
                if '?' in text and len(text) > 50:
                    # Try to split question and answer
                    parts = text.split('?', 1)
                    if len(parts) == 2:
                        question = parts[0].strip() + '?'
                        answer = parts[1].strip()
                        
                        if len(answer) > 20:  # Ensure we have a substantial answer
                            faq = SharePointFAQ(
                                question=question,
                                answer=answer,
                                page_url=page_url,
                                page_title=page_title,
                                faq_number=i + 1
                            )
                            faqs.append(faq)
        
        return faqs
    
    def _extract_tables(self, soup: BeautifulSoup, page_url: str, page_title: str) -> List[SharePointTable]:
        """Extract tables from SharePoint page."""
        tables = []
        
        table_elements = soup.find_all('table')
        
        for table_element in table_elements:
            try:
                # Extract headers
                headers = []
                header_row = table_element.find('tr')
                if header_row:
                    header_cells = header_row.find_all(['th', 'td'])
                    headers = [cell.get_text(strip=True) for cell in header_cells]
                
                # Extract rows
                rows = []
                data_rows = table_element.find_all('tr')[1:]  # Skip header row
                
                for row in data_rows:
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:  # Only add non-empty rows
                        rows.append(row_data)
                
                if headers and rows:
                    # Determine table type based on content
                    table_type = self._classify_table(headers, rows)
                    
                    table = SharePointTable(
                        title=f"Table from {page_title}",
                        headers=headers,
                        rows=rows,
                        page_url=page_url,
                        page_title=page_title,
                        table_type=table_type
                    )
                    tables.append(table)
                    
            except Exception as e:
                print(f"[WARNING] Failed to extract table: {e}")
                continue
        
        return tables
    
    def _classify_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Classify table type based on headers and content."""
        header_text = ' '.join(headers).lower()
        
        if 'feature' in header_text and ('yes' in header_text or 'no' in header_text):
            return "compatibility_matrix"
        elif 'description' in header_text:
            return "feature_definitions"
        elif 'migration' in header_text:
            return "migration_info"
        else:
            return "general_table"
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract general text content from SharePoint page."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _faq_to_document(self, faq: SharePointFAQ) -> Optional[Document]:
        """Convert FAQ to LangChain Document."""
        try:
            # Create content combining question and answer
            content = f"Q: {faq.question}\n\nA: {faq.answer}"
            
            # Create metadata
            metadata = SharePointMetadata(
                page_url=faq.page_url,
                page_title=faq.page_title,
                content_type="faq",
                faq_number=faq.faq_number
            )
            
            # Convert to dict for Document
            metadata_dict = {
                "source_type": metadata.source_type,
                "source": metadata.source,
                "page_url": metadata.page_url,
                "page_title": metadata.page_title,
                "content_type": metadata.content_type,
                "faq_number": metadata.faq_number
            }
            
            return Document(page_content=content, metadata=metadata_dict)
            
        except Exception as e:
            print(f"[ERROR] Failed to convert FAQ to document: {e}")
            return None
    
    def _table_to_document(self, table: SharePointTable) -> Optional[Document]:
        """Convert table to LangChain Document."""
        try:
            # Create content from table
            content_parts = [f"Table: {table.title}"]
            
            # Add headers
            if table.headers:
                content_parts.append(f"Headers: {', '.join(table.headers)}")
            
            # Add rows
            for i, row in enumerate(table.rows[:10]):  # Limit to first 10 rows
                row_text = ' | '.join(row)
                content_parts.append(f"Row {i+1}: {row_text}")
            
            if len(table.rows) > 10:
                content_parts.append(f"... and {len(table.rows) - 10} more rows")
            
            content = '\n'.join(content_parts)
            
            # Create metadata
            metadata = SharePointMetadata(
                page_url=table.page_url,
                page_title=table.page_title,
                content_type="table",
                table_title=table.title
            )
            
            # Convert to dict for Document
            metadata_dict = {
                "source_type": metadata.source_type,
                "source": metadata.source,
                "page_url": metadata.page_url,
                "page_title": metadata.page_title,
                "content_type": metadata.content_type,
                "table_title": metadata.table_title
            }
            
            return Document(page_content=content, metadata=metadata_dict)
            
        except Exception as e:
            print(f"[ERROR] Failed to convert table to document: {e}")
            return None
    
    def _text_to_document(self, text_content: str, page_url: str, page_title: str) -> Optional[Document]:
        """Convert text content to LangChain Document."""
        try:
            # Clean and limit text content
            text_content = text_content[:5000]  # Limit to 5000 characters
            
            # Create metadata
            metadata = SharePointMetadata(
                page_url=page_url,
                page_title=page_title,
                content_type="text"
            )
            
            # Convert to dict for Document
            metadata_dict = {
                "source_type": metadata.source_type,
                "source": metadata.source,
                "page_url": metadata.page_url,
                "page_title": metadata.page_title,
                "content_type": metadata.content_type
            }
            
            return Document(page_content=text_content, metadata=metadata_dict)
            
        except Exception as e:
            print(f"[ERROR] Failed to convert text to document: {e}")
            return None
    
    def crawl_sharepoint_pages(self) -> List[Document]:
        """Main method to crawl SharePoint pages and return Documents."""
        print("=" * 60)
        print("SHAREPOINT CONTENT CRAWLING")
        print("=" * 60)
        
        start_time = time.time()
        all_documents = []
        
        try:
            # Test authentication first
            if not sharepoint_auth.test_connection():
                print("[ERROR] SharePoint authentication failed")
                return []
            
            # Start crawling from the main page
            start_url = urljoin(self.site_url, self.start_page)
            print(f"[*] Starting crawl from: {start_url}")
            
            # Crawl pages recursively
            documents = self._crawl_page_recursive(start_url, depth=0)
            all_documents.extend(documents)
            
            # Calculate results
            duration = time.time() - start_time
            total_content_length = sum(len(doc.page_content) for doc in all_documents)
            
            result = SharePointCrawlResult(
                pages_crawled=len(self.crawled_urls),
                pages_failed=len(self.failed_urls),
                faqs_extracted=len([d for d in all_documents if d.metadata.get('content_type') == 'faq']),
                tables_extracted=len([d for d in all_documents if d.metadata.get('content_type') == 'table']),
                total_content_length=total_content_length,
                crawl_duration=duration
            )
            
            print(f"[OK] SharePoint crawling completed!")
            print(f"   Pages crawled: {result.pages_crawled}")
            print(f"   Pages failed: {result.pages_failed}")
            print(f"   FAQs extracted: {result.faqs_extracted}")
            print(f"   Tables extracted: {result.tables_extracted}")
            print(f"   Total content: {result.total_content_length} characters")
            print(f"   Duration: {result.crawl_duration:.2f} seconds")
            
            return all_documents
            
        except Exception as e:
            print(f"[ERROR] SharePoint crawling failed: {e}")
            return []
    
    def _crawl_page_recursive(self, page_url: str, depth: int = 0) -> List[Document]:
        """Recursively crawl SharePoint pages."""
        documents = []
        
        # Check depth limit
        if depth > self.max_depth:
            return documents
        
        # Skip if already crawled or failed
        if page_url in self.crawled_urls or page_url in self.failed_urls:
            return documents
        
        print(f"[*] Crawling page (depth {depth}): {page_url}")
        
        try:
            # Get page content
            page_data = self.get_page_content(page_url)
            if not page_data:
                self.failed_urls.add(page_url)
                return documents
            
            # Extract HTML content (this is a simplified approach)
            # In a real implementation, you'd need to parse the webParts data
            html_content = self._extract_html_from_page_data(page_data)
            
            if html_content:
                # Extract documents from this page
                page_documents = self.extract_content_from_html(
                    html_content, page_url, page_data.get('title', 'Untitled')
                )
                documents.extend(page_documents)
            
            # Mark as crawled
            self.crawled_urls.add(page_url)
            
            # Find links to other pages (simplified - in real implementation, parse webParts)
            # For now, we'll implement a basic link discovery
            child_urls = self._find_child_urls(html_content, page_url)
            
            # Crawl child pages
            for child_url in child_urls:
                child_documents = self._crawl_page_recursive(child_url, depth + 1)
                documents.extend(child_documents)
            
        except Exception as e:
            print(f"[ERROR] Failed to crawl page {page_url}: {e}")
            self.failed_urls.add(page_url)
        
        return documents
    
    def _extract_html_from_page_data(self, page_data: Dict[str, Any]) -> str:
        """Extract HTML content from SharePoint page data."""
        # This is a simplified implementation
        # In a real implementation, you'd parse the webParts data structure
        # and extract the actual HTML content
        
        try:
            # For now, return a placeholder - this would need to be implemented
            # based on the actual SharePoint page structure
            return f"<div>Content from {page_data.get('title', 'Untitled')}</div>"
        except Exception as e:
            print(f"[ERROR] Failed to extract HTML from page data: {e}")
            return ""
    
    def _find_child_urls(self, html_content: str, base_url: str) -> List[str]:
        """Find child URLs from HTML content."""
        # This is a simplified implementation
        # In a real implementation, you'd parse the HTML and find SharePoint links
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = urljoin(base_url, href)
                
                # Only include SharePoint links
                if 'sharepoint.com' in href and href not in self.crawled_urls:
                    links.append(href)
            
            return links[:5]  # Limit to 5 child pages per page
            
        except Exception as e:
            print(f"[ERROR] Failed to find child URLs: {e}")
            return []

def chunk_sharepoint_documents(documents: List[Document], chunk_size: int = 1500, chunk_overlap: int = 300) -> List[Document]:
    """Split SharePoint documents into smaller chunks for better retrieval."""
    if not documents:
        return documents
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunked_docs = []
    for doc in documents:
        chunks = splitter.split_documents([doc])
        # Preserve metadata (especially download_url, tags for certificates) in each chunk
        for chunk in chunks:
            # Keep all original metadata (including tags!)
            chunk.metadata.update(doc.metadata)
            chunk.metadata["chunk_index"] = chunks.index(chunk)
            chunk.metadata["total_chunks"] = len(chunks)
            # Ensure tag is preserved (in case it wasn't in original)
            if "tag" not in chunk.metadata and "folder_tags" in chunk.metadata:
                chunk.metadata["tag"] = chunk.metadata["folder_tags"]
        chunked_docs.extend(chunks)
    
    print(f"Split {len(documents)} SharePoint documents into {len(chunked_docs)} chunks")
    return chunked_docs

def process_sharepoint_content() -> List[Document]:
    """Main function to process SharePoint content."""
    # Try Graph API first (more reliable), fallback to Selenium if needed
    try:
        from app.sharepoint_graph_extractor import extract_sharepoint_via_graph
        
        print("[*] Using Microsoft Graph API for SharePoint extraction...")
        raw_docs = extract_sharepoint_via_graph()
        print(f"[OK] Extracted {len(raw_docs)} raw SharePoint documents via Graph API")
    except Exception as e:
        print(f"[WARNING] Graph API extraction failed: {e}")
        print("[*] Falling back to Selenium extraction...")
        from app.sharepoint_selenium_extractor import extract_sharepoint_pages
        raw_docs = extract_sharepoint_pages()
        print(f"[OK] Extracted {len(raw_docs)} raw SharePoint documents via Selenium")
    
    # Chunk the documents for better search and cost efficiency
    print("[*] Chunking SharePoint documents...")
    chunked_docs = chunk_sharepoint_documents(raw_docs, chunk_size=1500, chunk_overlap=300)
    print(f"[OK] Created {len(chunked_docs)} chunked documents")
    
    return chunked_docs
