"""
Unstructured library processor for complex document types.

Handles PPTX, complex PDFs with OCR, and extracts structured content
including tables, lists, headings, and image captions.
"""

import os
import tempfile
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
import requests

# Unstructured imports - graceful fallback if not installed
try:
    from unstructured.partition.auto import partition
    from unstructured.partition.pptx import partition_pptx
    from unstructured.partition.pdf import partition_pdf
    from unstructured.documents.elements import (
        Title, NarrativeText, ListItem, Table, Header, Footer, Image
    )
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    print("[WARNING] Unstructured library not available - complex file processing limited")


class UnstructuredProcessor:
    """
    Process complex documents using Unstructured library.
    """
    
    def __init__(self, enable_ocr: bool = True, ocr_language: str = "eng"):
        """
        Initialize Unstructured processor.
        
        Args:
            enable_ocr: Enable OCR for scanned PDFs
            ocr_language: Language for OCR (default: English)
        """
        self.enable_ocr = enable_ocr
        self.ocr_language = ocr_language
        
        if not UNSTRUCTURED_AVAILABLE:
            print("[WARNING] Unstructured library not available")
    
    def process_pptx(self, file_path: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Process PowerPoint file and extract content by slide.
        
        Args:
            file_path: Path to PPTX file
            metadata: Base metadata to attach
        
        Returns:
            List of Document objects (one per slide or logical section)
        """
        if not UNSTRUCTURED_AVAILABLE:
            print("[ERROR] Unstructured library required for PPTX processing")
            return []
        
        try:
            print(f"[*] Processing PPTX with Unstructured: {file_path}")
            
            # Partition PPTX into elements
            elements = partition_pptx(filename=file_path)
            
            # Group elements by slide/page
            slides = self._group_by_page(elements)
            
            documents = []
            for page_num, page_elements in slides.items():
                # Extract content from slide
                content_parts = []
                
                for element in page_elements:
                    if isinstance(element, Title):
                        content_parts.append(f"# {element.text}")
                    elif isinstance(element, Header):
                        content_parts.append(f"## {element.text}")
                    elif isinstance(element, ListItem):
                        content_parts.append(f"- {element.text}")
                    elif isinstance(element, Table):
                        content_parts.append(f"\nTable:\n{element.text}\n")
                    elif isinstance(element, NarrativeText):
                        content_parts.append(element.text)
                
                if content_parts:
                    slide_content = "\n\n".join(content_parts)
                    
                    doc_metadata = {
                        **(metadata or {}),
                        "page_number": page_num,
                        "content_type": "slide",
                        "element_count": len(page_elements)
                    }
                    
                    documents.append(Document(
                        page_content=slide_content,
                        metadata=doc_metadata
                    ))
            
            print(f"[OK] Extracted {len(documents)} slides from PPTX")
            return documents
            
        except Exception as e:
            print(f"[ERROR] Failed to process PPTX {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def process_pdf_with_ocr(
        self,
        file_path: str,
        metadata: Dict[str, Any] = None,
        force_ocr: bool = False
    ) -> List[Document]:
        """
        Process PDF with OCR support for scanned documents.
        
        Args:
            file_path: Path to PDF file
            metadata: Base metadata to attach
            force_ocr: Force OCR even if PDF has text
        
        Returns:
            List of Document objects
        """
        if not UNSTRUCTURED_AVAILABLE:
            print("[ERROR] Unstructured library required for OCR PDF processing")
            return []
        
        try:
            print(f"[*] Processing PDF with Unstructured (OCR={self.enable_ocr}): {file_path}")
            
            # Partition PDF with OCR support
            strategy = "ocr_only" if force_ocr else "auto"
            
            elements = partition_pdf(
                filename=file_path,
                strategy=strategy,
                ocr_languages=self.ocr_language if self.enable_ocr else None
            )
            
            # Group by page
            pages = self._group_by_page(elements)
            
            documents = []
            for page_num, page_elements in pages.items():
                # Extract structured content
                content_parts = []
                tables = []
                
                for element in page_elements:
                    if isinstance(element, Title):
                        content_parts.append(f"# {element.text}")
                    elif isinstance(element, Header):
                        content_parts.append(f"## {element.text}")
                    elif isinstance(element, ListItem):
                        content_parts.append(f"- {element.text}")
                    elif isinstance(element, Table):
                        # Store table separately
                        tables.append(element.text)
                        content_parts.append(f"\n[Table {len(tables)}]\n{element.text}\n")
                    elif isinstance(element, NarrativeText):
                        content_parts.append(element.text)
                
                if content_parts:
                    page_content = "\n\n".join(content_parts)
                    
                    doc_metadata = {
                        **(metadata or {}),
                        "page_number": page_num,
                        "content_type": "pdf_page",
                        "has_tables": len(tables) > 0,
                        "table_count": len(tables)
                    }
                    
                    documents.append(Document(
                        page_content=page_content,
                        metadata=doc_metadata
                    ))
            
            print(f"[OK] Extracted {len(documents)} pages from PDF")
            return documents
            
        except Exception as e:
            print(f"[ERROR] Failed to process PDF {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def process_file_auto(
        self,
        file_path: str,
        metadata: Dict[str, Any] = None
    ) -> List[Document]:
        """
        Auto-detect file type and process accordingly.
        
        Args:
            file_path: Path to file
            metadata: Base metadata to attach
        
        Returns:
            List of Document objects
        """
        if not UNSTRUCTURED_AVAILABLE:
            print("[ERROR] Unstructured library not available")
            return []
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pptx":
            return self.process_pptx(file_path, metadata)
        elif ext == ".pdf":
            return self.process_pdf_with_ocr(file_path, metadata)
        else:
            # Use auto partition for other types
            try:
                print(f"[*] Processing {ext} file with auto-partition")
                elements = partition(filename=file_path)
                
                # Convert elements to documents
                documents = self._elements_to_documents(elements, metadata)
                print(f"[OK] Extracted {len(documents)} chunks from {ext} file")
                return documents
            except Exception as e:
                print(f"[ERROR] Failed to process {file_path}: {e}")
                return []
    
    def process_from_url(
        self,
        url: str,
        metadata: Dict[str, Any] = None
    ) -> List[Document]:
        """
        Download and process file from URL.
        
        Args:
            url: File URL
            metadata: Base metadata
        
        Returns:
            List of Document objects
        """
        try:
            # Download file to temp directory
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Get file extension from URL or content-type
            ext = self._get_extension_from_url(url, response.headers.get('content-type', ''))
            
            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            try:
                # Process the temp file
                documents = self.process_file_auto(tmp_path, metadata)
                return documents
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
        except Exception as e:
            print(f"[ERROR] Failed to process file from URL {url}: {e}")
            return []
    
    def _group_by_page(self, elements: List) -> Dict[int, List]:
        """Group elements by page number."""
        pages = {}
        
        for element in elements:
            # Get page number from metadata
            page_num = 1  # Default
            if hasattr(element, 'metadata') and element.metadata:
                page_num = element.metadata.page_number if hasattr(element.metadata, 'page_number') else 1
            
            if page_num not in pages:
                pages[page_num] = []
            
            pages[page_num].append(element)
        
        return pages
    
    def _elements_to_documents(
        self,
        elements: List,
        metadata: Dict[str, Any] = None
    ) -> List[Document]:
        """Convert Unstructured elements to LangChain Documents."""
        documents = []
        
        # Group by page
        pages = self._group_by_page(elements)
        
        for page_num, page_elements in pages.items():
            content_parts = []
            
            for element in page_elements:
                text = str(element)
                if text.strip():
                    content_parts.append(text)
            
            if content_parts:
                page_content = "\n\n".join(content_parts)
                
                doc_metadata = {
                    **(metadata or {}),
                    "page_number": page_num
                }
                
                documents.append(Document(
                    page_content=page_content,
                    metadata=doc_metadata
                ))
        
        return documents
    
    def _get_extension_from_url(self, url: str, content_type: str = "") -> str:
        """Get file extension from URL or content type."""
        # Try to get from URL
        ext = os.path.splitext(url.split('?')[0])[1]
        if ext:
            return ext
        
        # Try to get from content-type
        if 'pdf' in content_type:
            return '.pdf'
        elif 'powerpoint' in content_type or 'presentation' in content_type:
            return '.pptx'
        elif 'word' in content_type or 'document' in content_type:
            return '.docx'
        elif 'excel' in content_type or 'spreadsheet' in content_type:
            return '.xlsx'
        
        return '.bin'


def process_complex_file(
    file_path: str,
    metadata: Dict[str, Any] = None,
    enable_ocr: bool = True
) -> List[Document]:
    """
    Convenience function to process complex files.
    
    Args:
        file_path: Path to file
        metadata: Base metadata
        enable_ocr: Enable OCR for scanned PDFs
    
    Returns:
        List of Document objects
    """
    processor = UnstructuredProcessor(enable_ocr=enable_ocr)
    return processor.process_file_auto(file_path, metadata)

