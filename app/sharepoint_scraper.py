# -*- coding: utf-8 -*-
"""
SharePoint Web Scraper

Uses web scraping to extract content from SharePoint pages since
Microsoft Graph API doesn't provide page content directly.
"""

import os
import requests
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

from app.sharepoint_auth import sharepoint_auth
from app.sharepoint_models import SharePointFAQ, SharePointTable, SharePointMetadata
from langchain_core.documents import Document

class SharePointWebScraper:
    """Scrapes SharePoint pages to extract content."""
    
    def __init__(self):
        self.site_url = os.getenv("SHAREPOINT_SITE_URL", "https://cloudfuzecom.sharepoint.com/sites/DOC360")
        self.start_page = os.getenv("SHAREPOINT_START_PAGE", "/SitePages/Multi%20User%20Golden%20Image%20Combinations.aspx")
        self.max_depth = int(os.getenv("SHAREPOINT_MAX_DEPTH", "3"))
        self.exclude_files = os.getenv("SHAREPOINT_EXCLUDE_FILES", "true").lower() == "true"
        
        # Track crawled URLs
        self.crawled_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        
        print(f"[*] SharePoint Web Scraper initialized")
        print(f"   Site URL: {self.site_url}")
        print(f"   Start Page: {self.start_page}")
    
    def scrape_page(self, page_url: str) -> Optional[Dict[str, Any]]:
        """Scrape a SharePoint page and extract its content."""
        try:
            print(f"[*] Scraping: {page_url}")
            
            # Create a session to maintain cookies
            session = requests.Session()
            
            # Use authenticated request with access token
            headers = sharepoint_auth.get_headers()
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            
            # Try to get the page with authentication
            response = session.get(page_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"[ERROR] Failed to fetch page: {response.status_code}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract page title
            title = soup.find('title')
            page_title = title.get_text() if title else 'Untitled'
            
            print(f"[OK] Scraped: {page_title}")
            
            return {
                'title': page_title,
                'url': page_url,
                'soup': soup,
                'html': response.text
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to scrape {page_url}: {e}")
            return None
    
    def find_child_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find all SharePoint links on the page."""
        links = []
        
        # Find all anchor tags
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            
            if not href:
                continue
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(base_url, href)
            elif href.startswith('http'):
                # Only include SharePoint links
                if 'sharepoint.com' in href:
                    links.append(href)
            
            # Check if it's a SharePoint page
            if 'sharepoint.com' in href and '/SitePages/' in href:
                if href not in links:
                    links.append(href)
        
        return links
    
    def extract_content(self, page_data: Dict[str, Any]) -> List[Document]:
        """Extract FAQs, tables, and text from a SharePoint page."""
        documents = []
        
        try:
            soup = page_data['soup']
            page_url = page_data['url']
            page_title = page_data['title']
            
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
            
            # Extract general text
            text_content = self._extract_text(soup)
            if text_content.strip():
                doc = self._text_to_document(text_content, page_url, page_title)
                if doc:
                    documents.append(doc)
            
            print(f"[OK] Extracted {len(faqs)} FAQs, {len(tables)} tables, 1 text block")
            
        except Exception as e:
            print(f"[ERROR] Failed to extract content: {e}")
        
        return documents
    
    def _extract_faqs(self, soup: BeautifulSoup, page_url: str, page_title: str) -> List[SharePointFAQ]:
        """Extract FAQ items from the page."""
        faqs = []
        
        # Look for patterns that indicate FAQs
        # Pattern 1: Numbered lists with questions
        
        # Find all paragraphs
        paragraphs = soup.find_all('p')
        
        current_question = None
        current_answer = []
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            
            if not text:
                if current_question and current_answer:
                    # Save previous FAQ
                    faq = SharePointFAQ(
                        question=current_question,
                        answer='\n'.join(current_answer),
                        page_url=page_url,
                        page_title=page_title,
                        faq_number=len(faqs) + 1
                    )
                    faqs.append(faq)
                    current_question = None
                    current_answer = []
                continue
            
            # Check if it's a question
            if '?' in text and len(text) > 20 and len(text) < 200:
                if current_question and current_answer:
                    # Save previous FAQ
                    faq = SharePointFAQ(
                        question=current_question,
                        answer='\n'.join(current_answer),
                        page_url=page_url,
                        page_title=page_title,
                        faq_number=len(faqs) + 1
                    )
                    faqs.append(faq)
                current_question = text
                current_answer = []
            elif current_question:
                current_answer.append(text)
        
        # Save last FAQ if exists
        if current_question and current_answer:
            faq = SharePointFAQ(
                question=current_question,
                answer='\n'.join(current_answer),
                page_url=page_url,
                page_title=page_title,
                faq_number=len(faqs) + 1
            )
            faqs.append(faq)
        
        return faqs
    
    def _extract_tables(self, soup: BeautifulSoup, page_url: str, page_title: str) -> List[SharePointTable]:
        """Extract tables from the page."""
        tables = []
        
        table_elements = soup.find_all('table')
        
        for i, table_element in enumerate(table_elements):
            try:
                # Extract headers
                headers = []
                header_row = table_element.find('tr')
                if header_row:
                    header_cells = header_row.find_all(['th', 'td'])
                    headers = [cell.get_text(strip=True) for cell in header_cells]
                
                # Extract rows
                rows = []
                data_rows = table_element.find_all('tr')[1:]
                
                for row in data_rows:
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:
                        rows.append(row_data)
                
                if headers and rows:
                    table = SharePointTable(
                        title=f"{page_title} - Table {i+1}",
                        headers=headers,
                        rows=rows,
                        page_url=page_url,
                        page_title=page_title,
                        table_type="compatibility_matrix" if 'Feature' in ' '.join(headers) else "general"
                    )
                    tables.append(table)
                    
            except Exception as e:
                print(f"[WARNING] Failed to extract table: {e}")
                continue
        
        return tables
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract general text content."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:5000]  # Limit to 5000 chars
    
    def _faq_to_document(self, faq: SharePointFAQ) -> Optional[Document]:
        """Convert FAQ to Document."""
        try:
            content = f"Q: {faq.question}\n\nA: {faq.answer}"
            
            metadata = SharePointMetadata(
                page_url=faq.page_url,
                page_title=faq.page_title,
                content_type="faq",
                faq_number=faq.faq_number
            )
            
            doc = Document(
                page_content=content,
                metadata={
                    "source_type": metadata.source_type,
                    "source": metadata.source,
                    "page_url": metadata.page_url,
                    "page_title": metadata.page_title,
                    "content_type": metadata.content_type,
                    "faq_number": metadata.faq_number
                }
            )
            
            return doc
            
        except Exception as e:
            print(f"[ERROR] Failed to convert FAQ to document: {e}")
            return None
    
    def _table_to_document(self, table: SharePointTable) -> Optional[Document]:
        """Convert table to Document."""
        try:
            content_parts = [f"Table: {table.title}"]
            content_parts.append(f"Headers: {', '.join(table.headers)}")
            
            for i, row in enumerate(table.rows[:10]):
                row_text = ' | '.join(row)
                content_parts.append(f"Row {i+1}: {row_text}")
            
            if len(table.rows) > 10:
                content_parts.append(f"... and {len(table.rows) - 10} more rows")
            
            content = '\n'.join(content_parts)
            
            metadata = SharePointMetadata(
                page_url=table.page_url,
                page_title=table.page_title,
                content_type="table"
            )
            
            doc = Document(
                page_content=content,
                metadata={
                    "source_type": metadata.source_type,
                    "source": metadata.source,
                    "page_url": metadata.page_url,
                    "page_title": metadata.page_title,
                    "content_type": metadata.content_type
                }
            )
            
            return doc
            
        except Exception as e:
            print(f"[ERROR] Failed to convert table to document: {e}")
            return None
    
    def _text_to_document(self, text: str, page_url: str, page_title: str) -> Optional[Document]:
        """Convert text to Document."""
        try:
            metadata = SharePointMetadata(
                page_url=page_url,
                page_title=page_title,
                content_type="text"
            )
            
            doc = Document(
                page_content=text,
                metadata={
                    "source_type": metadata.source_type,
                    "source": metadata.source,
                    "page_url": metadata.page_url,
                    "page_title": metadata.page_title,
                    "content_type": metadata.content_type
                }
            )
            
            return doc
            
        except Exception as e:
            print(f"[ERROR] Failed to convert text to document: {e}")
            return None
    
    def crawl_all_pages(self) -> List[Document]:
        """Crawl all SharePoint pages and extract content."""
        print("=" * 60)
        print("SHAREPOINT WEB SCRAPING - FULL CONTENT EXTRACTION")
        print("=" * 60)
        
        all_documents = []
        start_url = urljoin(self.site_url, self.start_page)
        
        print(f"[*] Starting from: {start_url}")
        print(f"[*] Max depth: {self.max_depth}")
        
        # Crawl recursively
        documents = self._crawl_recursive(start_url, depth=0)
        all_documents.extend(documents)
        
        print(f"\n[OK] Crawling complete!")
        print(f"   Pages crawled: {len(self.crawled_urls)}")
        print(f"   Documents extracted: {len(all_documents)}")
        
        return all_documents
    
    def _crawl_recursive(self, page_url: str, depth: int = 0) -> List[Document]:
        """Recursively crawl SharePoint pages."""
        documents = []
        
        # Check depth limit
        if depth > self.max_depth:
            return documents
        
        # Skip if already crawled or failed
        if page_url in self.crawled_urls or page_url in self.failed_urls:
            return documents
        
        try:
            # Scrape the page
            page_data = self.scrape_page(page_url)
            
            if page_data:
                # Extract content
                page_docs = self.extract_content(page_data)
                documents.extend(page_docs)
                
                # Mark as crawled
                self.crawled_urls.add(page_url)
                
                # Find child links
                child_links = self.find_child_links(page_data['soup'], page_url)
                
                # Crawl child pages
                for child_url in child_links[:5]:  # Limit to 5 children
                    if child_url not in self.crawled_urls:
                        time.sleep(1)  # Be polite
                        child_docs = self._crawl_recursive(child_url, depth + 1)
                        documents.extend(child_docs)
            else:
                self.failed_urls.add(page_url)
                
        except Exception as e:
            print(f"[ERROR] Failed to crawl {page_url}: {e}")
            self.failed_urls.add(page_url)
        
        return documents


def scrape_sharepoint_content() -> List[Document]:
    """Main function to scrape SharePoint content."""
    scraper = SharePointWebScraper()
    return scraper.crawl_all_pages()

if __name__ == "__main__":
    # Test the scraper
    docs = scrape_sharepoint_content()
    print(f"\n✅ Extracted {len(docs)} documents")
