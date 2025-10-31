# -*- coding: utf-8 -*-
"""
SharePoint File Processor

Unified processor that routes SharePoint files to appropriate processors
based on file type and creates standardized Document objects with rich metadata.
"""

import os
import tempfile
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import existing processors
from app.pdf_processor import extract_text_from_pdf
from app.doc_processor import extract_text_from_docx
from app.excel_processor import extract_text_from_excel
from app.powerpoint_processor import extract_text_from_pptx


class SharePointFileProcessor:
    """Processes files downloaded from SharePoint and creates Documents with metadata."""
    
    def __init__(self):
        """Initialize the file processor."""
        # Text splitter configurations by file type
        self.text_splitters = {
            'default': RecursiveCharacterTextSplitter(
                chunk_size=1500,
                chunk_overlap=300,
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len,
            ),
            'excel': RecursiveCharacterTextSplitter(
                chunk_size=2000,  # Larger chunks for tables
                chunk_overlap=200,
                separators=["\n\n", "\n", "---", " ", ""],
                length_function=len,
            ),
        }
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """
        Extract text from a file based on its type.
        
        Args:
            file_path: Path to the file
            file_type: File extension (without dot)
            
        Returns:
            Extracted text content
        """
        file_type = file_type.lower()
        
        try:
            if file_type == 'pdf':
                return extract_text_from_pdf(file_path)
            
            elif file_type in ['docx', 'doc']:
                return extract_text_from_docx(file_path)
            
            elif file_type in ['xlsx', 'xls']:
                # Excel processor returns Documents, so we need special handling
                return self._extract_excel_text(file_path)
            
            elif file_type in ['pptx', 'ppt']:
                return extract_text_from_pptx(file_path)
            
            elif file_type in ['txt', 'md']:
                return self._extract_plain_text(file_path)
            
            else:
                print(f"[WARNING] Unsupported file type: {file_type}")
                return ""
        
        except Exception as e:
            print(f"[ERROR] Failed to extract text from {file_path}: {e}")
            return ""
    
    def _extract_plain_text(self, file_path: str) -> str:
        """Extract text from plain text files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print(f"[ERROR] Failed to read text file: {e}")
                return ""
    
    def _extract_excel_text(self, file_path: str) -> str:
        """
        Extract text from Excel file.
        Excel files are processed as structured tables.
        """
        try:
            # Use the extract_text_from_excel function directly
            text = extract_text_from_excel(file_path)
            return text if text else ""
        
        except Exception as e:
            print(f"[ERROR] Failed to extract Excel text: {e}")
            return ""
    
    def _get_text_splitter(self, file_type: str) -> RecursiveCharacterTextSplitter:
        """Get appropriate text splitter for file type."""
        if file_type in ['xlsx', 'xls']:
            return self.text_splitters['excel']
        return self.text_splitters['default']
    
    def process_file(
        self, 
        file_path: str, 
        file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """
        Process a file and create Document objects with rich metadata.
        
        Args:
            file_path: Path to the downloaded file
            file_metadata: Metadata from SharePoint crawler
            
        Returns:
            List of Document objects with chunked content and metadata
        """
        file_name = file_metadata.get('file_name', 'unknown')
        file_type = file_metadata.get('file_type', '').lower()
        
        print(f"[*] Processing: {file_name}")
        
        # Extract text from file
        text_content = self.extract_text_from_file(file_path, file_type)
        
        if not text_content or not text_content.strip():
            print(f"[WARNING] No text extracted from {file_name}")
            return []
        
        print(f"[OK] Extracted {len(text_content)} characters")
        
        # Get appropriate text splitter
        text_splitter = self._get_text_splitter(file_type)
        
        # Split into chunks
        chunks = text_splitter.split_text(text_content)
        
        print(f"[OK] Split into {len(chunks)} chunks")
        
        # Create Document objects with comprehensive metadata
        documents = []
        
        for i, chunk in enumerate(chunks):
            # Create metadata for this chunk
            doc_metadata = {
                # Source information
                "source_type": file_metadata.get('source_type', 'sharepoint_document'),
                "source": file_metadata.get('source', 'cloudfuze_sharepoint'),
                
                # File information
                "file_name": file_name,
                "file_type": file_type,
                "sharepoint_url": file_metadata.get('sharepoint_url', ''),
                "folder_path": file_metadata.get('folder_path', ''),
                "drive_name": file_metadata.get('drive_name', ''),
                
                # File metadata
                "last_modified": file_metadata.get('last_modified', ''),
                "created": file_metadata.get('created', ''),
                "file_size_kb": file_metadata.get('file_size_kb', 0),
                
                # Chunk information
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            
            # Add file-type specific metadata
            if file_type == 'pdf':
                # For PDFs, we could add page numbers if we enhance the PDF processor
                doc_metadata['content_type'] = 'pdf_document'
            elif file_type in ['docx', 'doc']:
                doc_metadata['content_type'] = 'word_document'
            elif file_type in ['xlsx', 'xls']:
                doc_metadata['content_type'] = 'excel_spreadsheet'
            elif file_type in ['pptx', 'ppt']:
                doc_metadata['content_type'] = 'powerpoint_presentation'
            elif file_type in ['txt', 'md']:
                doc_metadata['content_type'] = 'text_file'
            
            # Create Document
            doc = Document(
                page_content=chunk,
                metadata=doc_metadata
            )
            
            documents.append(doc)
        
        return documents
    
    def process_file_batch(
        self, 
        files_with_metadata: List[Dict[str, Any]]
    ) -> List[Document]:
        """
        Process a batch of files.
        
        Args:
            files_with_metadata: List of file metadata dicts (must include 'local_path')
            
        Returns:
            List of all Document objects from all files
        """
        print(f"\n[*] Processing {len(files_with_metadata)} files...")
        
        all_documents = []
        successful = 0
        failed = 0
        
        for i, file_meta in enumerate(files_with_metadata, 1):
            file_name = file_meta.get('file_name', 'unknown')
            local_path = file_meta.get('local_path')
            
            if not local_path or not os.path.exists(local_path):
                print(f"[{i}/{len(files_with_metadata)}] [SKIP] File not found: {file_name}")
                failed += 1
                continue
            
            print(f"[{i}/{len(files_with_metadata)}] Processing: {file_name}")
            
            try:
                # Process the file
                docs = self.process_file(local_path, file_meta)
                
                if docs:
                    all_documents.extend(docs)
                    successful += 1
                    print(f"[OK] Created {len(docs)} document chunks")
                else:
                    failed += 1
                
            except Exception as e:
                print(f"[ERROR] Failed to process {file_name}: {e}")
                failed += 1
                continue
        
        print(f"\n[OK] Batch processing complete:")
        print(f"    Successful: {successful}")
        print(f"    Failed: {failed}")
        print(f"    Total documents: {len(all_documents)}")
        
        return all_documents
    
    def cleanup_temp_files(self, files_with_metadata: List[Dict[str, Any]]):
        """
        Clean up temporary downloaded files.
        
        Args:
            files_with_metadata: List of file metadata dicts with 'local_path'
        """
        print("\n[*] Cleaning up temporary files...")
        
        cleaned = 0
        for file_meta in files_with_metadata:
            local_path = file_meta.get('local_path')
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                    cleaned += 1
                except Exception as e:
                    print(f"[WARNING] Failed to delete {local_path}: {e}")
        
        print(f"[OK] Cleaned up {cleaned} temporary files")


def process_sharepoint_files(
    files_with_metadata: List[Dict[str, Any]],
    cleanup: bool = True
) -> List[Document]:
    """
    Convenience function to process SharePoint files.
    
    Args:
        files_with_metadata: List of file metadata from SharePoint crawler
        cleanup: Whether to clean up temporary files after processing
        
    Returns:
        List of Document objects
    """
    processor = SharePointFileProcessor()
    
    # Process all files
    documents = processor.process_file_batch(files_with_metadata)
    
    # Clean up if requested
    if cleanup:
        processor.cleanup_temp_files(files_with_metadata)
    
    return documents

