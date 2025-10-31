# -*- coding: utf-8 -*-
"""
SharePoint Page Content Parser

Parses SharePoint page content from Microsoft Graph API responses.
Extracts text, tables, lists, and other structured content from webParts.
"""

import re
import html
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup


class SharePointPageParser:
    """Parses SharePoint page content from Graph API responses."""
    
    def __init__(self):
        """Initialize the parser."""
        pass
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content and extract text."""
        if not html_content:
            return ""
        
        try:
            # Decode HTML entities
            html_content = html.unescape(html_content)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "meta", "link"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            print(f"[WARNING] Failed to clean HTML: {e}")
            return html_content
    
    def _extract_tables_from_html(self, html_content: str) -> List[str]:
        """Extract tables from HTML and format as markdown."""
        tables = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            table_elements = soup.find_all('table')
            
            for table in table_elements:
                try:
                    # Extract headers
                    headers = []
                    header_row = table.find('tr')
                    if header_row:
                        header_cells = header_row.find_all(['th', 'td'])
                        headers = [cell.get_text(strip=True) for cell in header_cells]
                    
                    # Extract rows
                    rows = []
                    data_rows = table.find_all('tr')[1:] if headers else table.find_all('tr')
                    
                    for row in data_rows:
                        cells = row.find_all(['td', 'th'])
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        if row_data and any(row_data):  # Only add non-empty rows
                            rows.append(row_data)
                    
                    if headers or rows:
                        # Format as markdown table
                        table_md = "\n\n**Table:**\n\n"
                        
                        if headers:
                            table_md += "| " + " | ".join(headers) + " |\n"
                            table_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                        
                        for row in rows:
                            # Pad row to match headers length if needed
                            if headers and len(row) < len(headers):
                                row = row + [""] * (len(headers) - len(row))
                            table_md += "| " + " | ".join(row) + " |\n"
                        
                        tables.append(table_md)
                        
                except Exception as e:
                    print(f"[WARNING] Failed to extract table: {e}")
                    continue
            
        except Exception as e:
            print(f"[WARNING] Failed to extract tables from HTML: {e}")
        
        return tables
    
    def _parse_webpart(self, webpart: Dict[str, Any]) -> str:
        """Parse a single webPart and extract content."""
        content_parts = []
        
        try:
            # Get webpart type
            webpart_type = webpart.get('webPartType', '')
            
            # Get inner HTML content
            inner_html = webpart.get('innerHtml', '')
            
            if inner_html:
                # Extract tables first (before cleaning HTML)
                tables = self._extract_tables_from_html(inner_html)
                
                # Extract clean text
                text = self._clean_html(inner_html)
                
                if text:
                    content_parts.append(text)
                
                # Add tables
                if tables:
                    content_parts.extend(tables)
            
            # Handle webPartData if present
            webpart_data = webpart.get('webPartData', {})
            if webpart_data:
                # Some webparts store data in properties
                properties = webpart_data.get('properties', {})
                
                # Extract text properties
                for key, value in properties.items():
                    if isinstance(value, str) and value and len(value) > 10:
                        # Clean and add if it looks like content
                        clean_value = self._clean_html(value)
                        if clean_value:
                            content_parts.append(clean_value)
            
        except Exception as e:
            print(f"[WARNING] Failed to parse webpart: {e}")
        
        return "\n\n".join(content_parts)
    
    def _parse_canvas_layout(self, canvas_layout: Dict[str, Any]) -> str:
        """Parse the canvas layout structure and extract content."""
        content_parts = []
        
        try:
            # Parse horizontal sections
            horizontal_sections = canvas_layout.get('horizontalSections', [])
            
            for section in horizontal_sections:
                columns = section.get('columns', [])
                
                for column in columns:
                    webparts = column.get('webparts', [])
                    
                    for webpart in webparts:
                        webpart_content = self._parse_webpart(webpart)
                        if webpart_content:
                            content_parts.append(webpart_content)
            
            # Parse vertical section
            vertical_section = canvas_layout.get('verticalSection', {})
            if vertical_section:
                webparts = vertical_section.get('webparts', [])
                
                for webpart in webparts:
                    webpart_content = self._parse_webpart(webpart)
                    if webpart_content:
                        content_parts.append(webpart_content)
            
        except Exception as e:
            print(f"[WARNING] Failed to parse canvas layout: {e}")
        
        return "\n\n".join(content_parts)
    
    def parse_page_content(self, page_data: Dict[str, Any]) -> str:
        """
        Parse SharePoint page content from Graph API response.
        
        Args:
            page_data: Page data from Graph API
            
        Returns:
            Extracted text content
        """
        content_parts = []
        
        try:
            # Add page title
            title = page_data.get('title', '')
            if title:
                content_parts.append(f"# {title}\n")
            
            # Add page description if available
            description = page_data.get('description', '')
            if description:
                content_parts.append(f"{description}\n")
            
            # Parse canvas layout (main content)
            canvas_layout = page_data.get('canvasLayout', {})
            if canvas_layout:
                canvas_content = self._parse_canvas_layout(canvas_layout)
                if canvas_content:
                    content_parts.append(canvas_content)
            
            # Fallback: try to get content from other fields
            if not content_parts or len(content_parts) <= 1:
                # Try webParts field (older API version)
                webparts = page_data.get('webParts', [])
                for webpart in webparts:
                    webpart_content = self._parse_webpart(webpart)
                    if webpart_content:
                        content_parts.append(webpart_content)
            
            # Join all content
            full_content = "\n\n".join(content_parts)
            
            # Final cleanup
            full_content = full_content.strip()
            
            return full_content
            
        except Exception as e:
            print(f"[ERROR] Failed to parse page content: {e}")
            return ""
    
    def extract_links_from_content(self, content: str) -> List[str]:
        """
        Extract URLs from content text.
        
        Args:
            content: Text content
            
        Returns:
            List of URLs found in content
        """
        links = []
        
        try:
            # Pattern to match URLs
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            
            matches = re.findall(url_pattern, content)
            links.extend(matches)
            
            # Remove duplicates
            links = list(set(links))
            
        except Exception as e:
            print(f"[WARNING] Failed to extract links: {e}")
        
        return links

