#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SharePoint Document Extraction Script

Orchestrates the complete process of:
1. Crawling SharePoint DOC360 site for documents
2. Downloading files (PDF, Word, Excel, PowerPoint, text)
3. Processing and chunking documents
4. Generating embeddings
5. Storing in MongoDB Atlas vector store

This script can be run multiple times to add new/updated documents
without duplicating existing content (smart duplicate detection).
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.sharepoint_document_crawler import get_sharepoint_crawler
from app.sharepoint_page_crawler import get_sharepoint_page_crawler
from app.sharepoint_file_processor import SharePointFileProcessor
from app.mongodb_vectorstore import MongoDBVectorStore
from config import (
    MONGODB_VECTORSTORE_COLLECTION,
    EXTRACT_SHAREPOINT_PAGES,
    EXTRACT_SHAREPOINT_FILES
)


class SharePointExtractor:
    """Main orchestrator for SharePoint document extraction."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.log_file = "data/sharepoint_extraction_log.json"
        self.summary_file = "data/sharepoint_extraction_summary.json"
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Load processing log
        self.processing_log = self._load_processing_log()
        
        # Statistics
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "pages_crawled": 0,
            "pages_skipped": 0,
            "page_chunks_created": 0,
            "files_crawled": 0,
            "files_downloaded": 0,
            "files_processed": 0,
            "files_skipped": 0,
            "files_updated": 0,
            "file_chunks_created": 0,
            "total_chunks_stored": 0,
            "errors": []
        }
    
    def _load_processing_log(self) -> Dict[str, Any]:
        """Load the processing log from disk."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load processing log: {e}")
                return {}
        return {}
    
    def _save_processing_log(self):
        """Save the processing log to disk."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.processing_log, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save processing log: {e}")
    
    def _get_file_hash(self, file_metadata: Dict[str, Any]) -> str:
        """Create unique hash for a file based on URL, name, and last modified date."""
        key = f"{file_metadata['sharepoint_url']}|{file_metadata['file_name']}|{file_metadata['last_modified']}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _should_process_file(self, file_metadata: Dict[str, Any]) -> tuple[bool, str]:
        """
        Determine if a file should be processed.
        
        Returns:
            (should_process, reason)
        """
        file_hash = self._get_file_hash(file_metadata)
        file_name = file_metadata['file_name']
        
        # Check if file has been processed before
        if file_hash in self.processing_log:
            return False, f"Already processed (up to date)"
        
        # Check if an older version exists
        file_url = file_metadata['sharepoint_url']
        for existing_hash, log_entry in self.processing_log.items():
            if log_entry.get('sharepoint_url') == file_url:
                return True, f"File updated (will replace old version)"
        
        # New file
        return True, "New file"
    
    def _remove_old_chunks_from_mongodb(
        self, 
        vectorstore: MongoDBVectorStore, 
        file_metadata: Dict[str, Any]
    ):
        """Remove old chunks of a file from MongoDB before adding new ones."""
        try:
            file_url = file_metadata['sharepoint_url']
            file_name = file_metadata['file_name']
            
            # Query MongoDB for existing chunks
            query = {
                "metadata.sharepoint_url": file_url,
                "metadata.file_name": file_name
            }
            
            # Count existing chunks
            existing_count = vectorstore.collection.count_documents(query)
            
            if existing_count > 0:
                print(f"[*] Found {existing_count} existing chunks for {file_name}, removing...")
                vectorstore.collection.delete_many(query)
                print(f"[OK] Removed {existing_count} old chunks")
                self.stats['files_updated'] += 1
            
        except Exception as e:
            print(f"[WARNING] Failed to remove old chunks: {e}")
    
    def extract_sharepoint_pages(self) -> List:
        """Extract SharePoint page content."""
        print("\n" + "=" * 70)
        print("STEP 1: EXTRACTING SHAREPOINT PAGES")
        print("=" * 70)
        
        if not EXTRACT_SHAREPOINT_PAGES:
            print("[*] Page extraction disabled (EXTRACT_SHAREPOINT_PAGES=false)")
            return []
        
        try:
            # Get page crawler
            page_crawler = get_sharepoint_page_crawler()
            
            # Crawl pages
            page_documents = page_crawler.crawl()
            
            self.stats['pages_crawled'] = page_crawler.stats['pages_crawled']
            self.stats['pages_skipped'] = page_crawler.stats['pages_skipped']
            
            if page_documents:
                # Chunk page documents
                print(f"\n[*] Chunking {len(page_documents)} page documents...")
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1500,
                    chunk_overlap=300,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
                
                chunked_docs = text_splitter.split_documents(page_documents)
                
                # Update chunk indices
                for i, doc in enumerate(chunked_docs):
                    doc.metadata['chunk_index'] = i
                    doc.metadata['total_chunks'] = len(chunked_docs)
                
                self.stats['page_chunks_created'] = len(chunked_docs)
                print(f"[OK] Created {len(chunked_docs)} page chunks")
                
                return chunked_docs
            
            return []
            
        except Exception as e:
            error_msg = f"Failed to extract SharePoint pages: {e}"
            print(f"[ERROR] {error_msg}")
            self.stats['errors'].append(error_msg)
            import traceback
            traceback.print_exc()
            return []
    
    def crawl_sharepoint_files(self) -> List[Dict[str, Any]]:
        """Crawl SharePoint site and get list of files."""
        print("\n" + "=" * 70)
        print("STEP 2: CRAWLING SHAREPOINT FILES")
        print("=" * 70)
        
        if not EXTRACT_SHAREPOINT_FILES:
            print("[*] File extraction disabled (EXTRACT_SHAREPOINT_FILES=false)")
            return []
        
        try:
            # Get crawler instance
            crawler = get_sharepoint_crawler()
            
            # Crawl site
            files_metadata = crawler.crawl_site()
            
            self.stats['files_crawled'] = len(files_metadata)
            
            return files_metadata
            
        except Exception as e:
            error_msg = f"Failed to crawl SharePoint: {e}"
            print(f"[ERROR] {error_msg}")
            self.stats['errors'].append(error_msg)
            return []
    
    def download_files(
        self, 
        files_metadata: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Download files from SharePoint."""
        print("\n" + "=" * 70)
        print("STEP 3: DOWNLOADING FILES")
        print("=" * 70)
        
        # Filter files that need processing
        files_to_download = []
        
        for file_meta in files_metadata:
            should_process, reason = self._should_process_file(file_meta)
            
            if should_process:
                files_to_download.append(file_meta)
                print(f"[*] Will process: {file_meta['file_name']} ({reason})")
            else:
                print(f"[SKIP] {file_meta['file_name']} ({reason})")
                self.stats['files_skipped'] += 1
        
        if not files_to_download:
            print("\n[*] No new files to download")
            return []
        
        print(f"\n[*] Downloading {len(files_to_download)} files...")
        
        try:
            # Get crawler to download files
            crawler = get_sharepoint_crawler()
            
            # Download files
            downloaded_files = crawler.download_file_batch(files_to_download)
            
            self.stats['files_downloaded'] = len(downloaded_files)
            
            return downloaded_files
            
        except Exception as e:
            error_msg = f"Failed to download files: {e}"
            print(f"[ERROR] {error_msg}")
            self.stats['errors'].append(error_msg)
            return []
    
    def process_files(
        self, 
        downloaded_files: List[Dict[str, Any]]
    ) -> List:
        """Process downloaded files into Document objects."""
        print("\n" + "=" * 70)
        print("STEP 4: PROCESSING FILES")
        print("=" * 70)
        
        if not downloaded_files:
            print("[*] No files to process")
            return []
        
        try:
            # Initialize file processor
            processor = SharePointFileProcessor()
            
            # Process files
            documents = processor.process_file_batch(downloaded_files)
            
            self.stats['files_processed'] = len(downloaded_files)
            self.stats['file_chunks_created'] = len(documents)
            
            return documents
            
        except Exception as e:
            error_msg = f"Failed to process files: {e}"
            print(f"[ERROR] {error_msg}")
            self.stats['errors'].append(error_msg)
            return []
    
    def store_in_mongodb(self, documents: List) -> bool:
        """Store documents in MongoDB Atlas vector store."""
        print("\n" + "=" * 70)
        print("STEP 5: STORING IN MONGODB VECTOR STORE")
        print("=" * 70)
        
        if not documents:
            print("[*] No documents to store")
            return True
        
        try:
            # Initialize embeddings
            print("[*] Initializing OpenAI embeddings...")
            embeddings = OpenAIEmbeddings()
            
            # Initialize MongoDB vector store
            print(f"[*] Connecting to MongoDB vector store...")
            vectorstore = MongoDBVectorStore(
                collection_name=MONGODB_VECTORSTORE_COLLECTION,
                embedding_function=embeddings
            )
            
            # Group documents by file for batch processing
            files_docs = {}
            for doc in documents:
                file_name = doc.metadata.get('file_name', 'unknown')
                if file_name not in files_docs:
                    files_docs[file_name] = []
                files_docs[file_name].append(doc)
            
            # Process each file
            total_stored = 0
            
            for file_name, file_docs in files_docs.items():
                print(f"\n[*] Storing {len(file_docs)} chunks from {file_name}...")
                
                # Remove old chunks if file was updated
                if file_docs:
                    self._remove_old_chunks_from_mongodb(vectorstore, file_docs[0].metadata)
                
                # Add new chunks
                try:
                    doc_ids = vectorstore.add_documents(file_docs)
                    total_stored += len(doc_ids)
                    print(f"[OK] Stored {len(doc_ids)} chunks")
                    
                    # Update processing log
                    file_hash = self._get_file_hash(file_docs[0].metadata)
                    self.processing_log[file_hash] = {
                        'file_name': file_name,
                        'sharepoint_url': file_docs[0].metadata.get('sharepoint_url', ''),
                        'last_modified': file_docs[0].metadata.get('last_modified', ''),
                        'chunks_stored': len(doc_ids),
                        'processed_at': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    error_msg = f"Failed to store {file_name}: {e}"
                    print(f"[ERROR] {error_msg}")
                    self.stats['errors'].append(error_msg)
                    continue
            
            self.stats['total_chunks_stored'] = total_stored
            
            # Save processing log
            self._save_processing_log()
            
            # Get final statistics
            stats = vectorstore.get_collection_stats()
            print(f"\n[OK] MongoDB Vector Store Statistics:")
            print(f"    Total documents in collection: {stats['total_documents']}")
            print(f"    Embedding dimension: {stats['embedding_dimension']}")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to store in MongoDB: {e}"
            print(f"[ERROR] {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
    
    def save_summary(self):
        """Save extraction summary to file."""
        self.stats['end_time'] = datetime.now().isoformat()
        
        # Calculate duration
        start = datetime.fromisoformat(self.stats['start_time'])
        end = datetime.fromisoformat(self.stats['end_time'])
        duration = (end - start).total_seconds()
        self.stats['duration_seconds'] = round(duration, 2)
        
        # Save summary
        try:
            with open(self.summary_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
            print(f"\n[OK] Summary saved to: {self.summary_file}")
        except Exception as e:
            print(f"[WARNING] Failed to save summary: {e}")
    
    def print_summary(self):
        """Print extraction summary."""
        print("\n" + "=" * 70)
        print("EXTRACTION COMPLETE - SUMMARY")
        print("=" * 70)
        print(f"Pages crawled: {self.stats['pages_crawled']}")
        print(f"Pages skipped: {self.stats['pages_skipped']}")
        print(f"Page chunks created: {self.stats['page_chunks_created']}")
        print(f"Files crawled: {self.stats['files_crawled']}")
        print(f"Files downloaded: {self.stats['files_downloaded']}")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files skipped (already current): {self.stats['files_skipped']}")
        print(f"Files updated: {self.stats['files_updated']}")
        print(f"File chunks created: {self.stats['file_chunks_created']}")
        print(f"Total chunks stored in MongoDB: {self.stats['total_chunks_stored']}")
        print(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats.get('duration_seconds'):
            print(f"Duration: {self.stats['duration_seconds']} seconds")
        
        if self.stats['errors']:
            print("\nErrors encountered:")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")
        
        print("=" * 70)
        
        if self.stats['total_chunks_stored'] > 0:
            print("\n✅ SUCCESS! SharePoint documents added to MongoDB vector store")
            print("   Your RAG model now has access to this knowledge base!")
            print("   No deployment needed - changes are live immediately.")
        else:
            print("\n⚠️  No new documents were added")
    
    def run(self):
        """Run the complete extraction process."""
        print("\n" + "=" * 70)
        print("SHAREPOINT DOCUMENT EXTRACTION")
        print("=" * 70)
        print(f"Target Site: {os.getenv('SHAREPOINT_SITE_URL')}")
        print(f"MongoDB Collection: {MONGODB_VECTORSTORE_COLLECTION}")
        print(f"Extract Pages: {EXTRACT_SHAREPOINT_PAGES}")
        print(f"Extract Files: {EXTRACT_SHAREPOINT_FILES}")
        print("=" * 70)
        
        all_documents = []
        
        try:
            # Step 1: Extract SharePoint Pages
            page_documents = self.extract_sharepoint_pages()
            if page_documents:
                all_documents.extend(page_documents)
            
            # Step 2: Crawl SharePoint Files
            files_metadata = self.crawl_sharepoint_files()
            
            # Step 3: Download files (if any)
            if files_metadata:
                downloaded_files = self.download_files(files_metadata)
                
                # Step 4: Process files
                if downloaded_files:
                    file_documents = self.process_files(downloaded_files)
                    if file_documents:
                        all_documents.extend(file_documents)
                        
                        # Clean up temporary files
                        print("\n[*] Cleaning up temporary files...")
                        processor = SharePointFileProcessor()
                        processor.cleanup_temp_files(downloaded_files)
            
            # Step 5: Store all documents in MongoDB
            if all_documents:
                success = self.store_in_mongodb(all_documents)
            else:
                print("\n[*] No documents to store")
                
            # Check what was extracted
            if not page_documents and not files_metadata:
                print("\n[WARNING] No pages or files found/extracted")
                print("          Check your configuration:")
                print(f"          EXTRACT_SHAREPOINT_PAGES={EXTRACT_SHAREPOINT_PAGES}")
                print(f"          EXTRACT_SHAREPOINT_FILES={EXTRACT_SHAREPOINT_FILES}")
            
            
        except KeyboardInterrupt:
            print("\n\n[*] Extraction interrupted by user")
        except Exception as e:
            print(f"\n[ERROR] Extraction failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always save summary
            self.save_summary()
            self.print_summary()


def main():
    """Main entry point."""
    # Check required environment variables
    required_vars = [
        'OPENAI_API_KEY',
        'MICROSOFT_CLIENT_ID',
        'MICROSOFT_CLIENT_SECRET',
        'SHAREPOINT_SITE_URL',
        'MONGODB_URL'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("[ERROR] Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables in your .env file")
        sys.exit(1)
    
    # Run extraction
    extractor = SharePointExtractor()
    extractor.run()


if __name__ == "__main__":
    main()

