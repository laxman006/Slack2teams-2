# -*- coding: utf-8 -*-
"""
SharePoint Data Models

Data models for SharePoint content processing and storage.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class SharePointPage:
    """Represents a SharePoint page with its content and metadata."""
    
    url: str
    title: str
    content: str
    content_type: str  # 'faq', 'table', 'text', 'hub'
    last_modified: Optional[datetime] = None
    crawl_depth: int = 0
    parent_url: Optional[str] = None
    child_urls: List[str] = None
    
    def __post_init__(self):
        if self.child_urls is None:
            self.child_urls = []

@dataclass
class SharePointFAQ:
    """Represents a FAQ item extracted from SharePoint."""
    
    question: str
    answer: str
    page_url: str
    page_title: str
    faq_number: Optional[int] = None

@dataclass
class SharePointTable:
    """Represents a table extracted from SharePoint."""
    
    title: str
    headers: List[str]
    rows: List[List[str]]
    page_url: str
    page_title: str
    table_type: str = "compatibility_matrix"  # or "feature_definitions", etc.

@dataclass
class SharePointCrawlResult:
    """Result of SharePoint crawling operation."""
    
    pages_crawled: int
    pages_failed: int
    faqs_extracted: int
    tables_extracted: int
    total_content_length: int
    crawl_duration: float
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

@dataclass
class SharePointMetadata:
    """Metadata for SharePoint content in vectorstore."""
    
    source_type: str = "sharepoint"
    source: str = "cloudfuze_doc360"
    page_url: str = ""
    page_title: str = ""
    content_type: str = ""
    last_modified: str = ""
    crawl_depth: int = 0
    faq_number: Optional[int] = None
    table_title: Optional[str] = None
