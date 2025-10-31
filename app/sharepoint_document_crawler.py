# -*- coding: utf-8 -*-
"""
SharePoint Document Crawler

Crawls SharePoint DOC360 site using Microsoft Graph API to:
- List all document libraries
- Recursively traverse folders
- Download supported document files (PDF, Word, Excel, PowerPoint, text)
- Skip images and videos
- Track comprehensive metadata for citations
"""

import os
import requests
import hashlib
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlparse, quote
from datetime import datetime
import tempfile
import time


class SharePointDocumentCrawler:
    """Crawls SharePoint site and downloads documents using Microsoft Graph API."""
    
    # File extensions to include
    SUPPORTED_EXTENSIONS = {
        '.pdf', '.docx', '.doc', '.xlsx', '.xls', 
        '.pptx', '.ppt', '.txt', '.md'
    }
    
    # File extensions to skip
    SKIP_EXTENSIONS = {
        # Images
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff',
        # Videos
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v',
        # Other binary/media
        '.zip', '.rar', '.7z', '.tar', '.gz', '.exe', '.dll', '.bin',
        '.mp3', '.wav', '.ogg', '.m4a', '.flac'
    }
    
    def __init__(self, site_url: str, auth_headers: Dict[str, str], max_file_size_mb: int = 50):
        """
        Initialize SharePoint document crawler.
        
        Args:
            site_url: SharePoint site URL (e.g., https://cloudfuzecom.sharepoint.com/sites/DOC360)
            auth_headers: Authentication headers with Bearer token
            max_file_size_mb: Maximum file size to download in MB
        """
        self.site_url = site_url
        self.auth_headers = auth_headers
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        # Parse site URL to extract components
        parsed_url = urlparse(site_url)
        self.hostname = parsed_url.netloc
        self.site_path = parsed_url.path
        
        # Statistics tracking
        self.files_found = 0
        self.files_downloaded = 0
        self.files_skipped = 0
        self.errors = []
        
        # Track processed files to avoid duplicates
        self.processed_urls: Set[str] = set()
        
        print(f"[*] SharePoint Document Crawler initialized")
        print(f"    Site: {site_url}")
        print(f"    Max file size: {max_file_size_mb} MB")
    
    def _get_site_id(self) -> Optional[str]:
        """Get SharePoint site ID using Graph API."""
        try:
            # Construct Graph API URL for site
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{self.hostname}:{self.site_path}"
            
            print(f"[*] Getting site ID from: {graph_url}")
            response = requests.get(graph_url, headers=self.auth_headers, timeout=30)
            response.raise_for_status()
            
            site_data = response.json()
            site_id = site_data.get('id')
            site_name = site_data.get('name', 'Unknown')
            
            print(f"[OK] Found site: {site_name} (ID: {site_id})")
            return site_id
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get site ID: {e}")
            return None
    
    def _get_drives(self, site_id: str) -> List[Dict[str, Any]]:
        """Get all document libraries (drives) in the site."""
        try:
            drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            
            print(f"[*] Getting document libraries...")
            response = requests.get(drives_url, headers=self.auth_headers, timeout=30)
            response.raise_for_status()
            
            drives_data = response.json()
            drives = drives_data.get('value', [])
            
            print(f"[OK] Found {len(drives)} document libraries:")
            for drive in drives:
                print(f"    - {drive.get('name')} (ID: {drive.get('id')})")
            
            return drives
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get drives: {e}")
            return []
    
    def _list_folder_contents(self, drive_id: str, item_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List contents of a folder in a drive.
        
        Args:
            drive_id: Drive ID
            item_id: Item ID (None for root folder)
        """
        try:
            if item_id:
                url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/children"
            else:
                url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
            
            items = []
            
            # Handle pagination
            while url:
                response = requests.get(url, headers=self.auth_headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                items.extend(data.get('value', []))
                
                # Check for next page
                url = data.get('@odata.nextLink')
            
            return items
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to list folder contents: {e}")
            return []
    
    def _should_process_file(self, item: Dict[str, Any]) -> bool:
        """Determine if a file should be processed."""
        file_name = item.get('name', '').lower()
        
        # Check file extension
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # Skip if in skip list
        if file_ext in self.SKIP_EXTENSIONS:
            return False
        
        # Only process if in supported list
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            return False
        
        # Check file size
        file_size = item.get('size', 0)
        if file_size > self.max_file_size_bytes:
            print(f"[SKIP] File too large: {file_name} ({file_size / 1024 / 1024:.1f} MB)")
            self.files_skipped += 1
            return False
        
        # Check if already processed
        web_url = item.get('webUrl', '')
        if web_url in self.processed_urls:
            return False
        
        return True
    
    def _extract_file_metadata(self, item: Dict[str, Any], drive_name: str, folder_path: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from a file item."""
        file_name = item.get('name', 'unknown')
        file_ext = os.path.splitext(file_name)[1].lower()
        
        metadata = {
            'file_name': file_name,
            'file_type': file_ext.lstrip('.'),
            'sharepoint_url': item.get('webUrl', ''),
            'download_url': item.get('@microsoft.graph.downloadUrl', ''),
            'folder_path': folder_path,
            'drive_name': drive_name,
            'file_size_kb': round(item.get('size', 0) / 1024, 2),
            'last_modified': item.get('lastModifiedDateTime', ''),
            'created': item.get('createdDateTime', ''),
            'item_id': item.get('id', ''),
            'source_type': 'sharepoint_document',
            'source': 'cloudfuze_sharepoint'
        }
        
        return metadata
    
    def _download_file(self, download_url: str, file_name: str) -> Optional[str]:
        """
        Download a file and save to temporary location.
        
        Returns:
            Path to downloaded file, or None if download failed
        """
        try:
            # Download file
            response = requests.get(download_url, timeout=120, stream=True)
            response.raise_for_status()
            
            # Save to temporary file
            file_ext = os.path.splitext(file_name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                temp_path = tmp_file.name
            
            self.files_downloaded += 1
            return temp_path
            
        except Exception as e:
            error_msg = f"Failed to download {file_name}: {e}"
            print(f"[ERROR] {error_msg}")
            self.errors.append(error_msg)
            return None
    
    def _crawl_folder_recursive(
        self, 
        drive_id: str, 
        drive_name: str,
        item_id: Optional[str] = None, 
        current_path: str = "",
        depth: int = 0,
        max_depth: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recursively crawl folders and collect file information.
        
        Returns:
            List of file metadata dictionaries
        """
        if depth > max_depth:
            return []
        
        files_info = []
        
        # List folder contents
        items = self._list_folder_contents(drive_id, item_id)
        
        for item in items:
            item_name = item.get('name', 'unknown')
            
            # Check if it's a folder
            if 'folder' in item:
                # Recursively crawl subfolder
                subfolder_path = f"{current_path}/{item_name}" if current_path else item_name
                print(f"[*] Entering folder: {subfolder_path}")
                
                subfolder_files = self._crawl_folder_recursive(
                    drive_id, 
                    drive_name,
                    item.get('id'),
                    subfolder_path,
                    depth + 1,
                    max_depth
                )
                files_info.extend(subfolder_files)
            
            # Check if it's a file we should process
            elif 'file' in item:
                self.files_found += 1
                
                if self._should_process_file(item):
                    # Extract metadata
                    file_metadata = self._extract_file_metadata(item, drive_name, current_path)
                    
                    # Mark as processed
                    self.processed_urls.add(file_metadata['sharepoint_url'])
                    
                    files_info.append(file_metadata)
                    print(f"[OK] Found: {item_name} ({file_metadata['file_size_kb']} KB)")
                else:
                    self.files_skipped += 1
        
        return files_info
    
    def crawl_site(self) -> List[Dict[str, Any]]:
        """
        Crawl the entire SharePoint site and collect all document metadata.
        
        Returns:
            List of file metadata dictionaries
        """
        print("=" * 70)
        print("SHAREPOINT DOCUMENT CRAWLER - STARTING")
        print("=" * 70)
        
        start_time = time.time()
        all_files = []
        
        # Get site ID
        site_id = self._get_site_id()
        if not site_id:
            print("[ERROR] Could not get site ID")
            return []
        
        # Get all document libraries
        drives = self._get_drives(site_id)
        if not drives:
            print("[ERROR] No document libraries found")
            return []
        
        # Crawl each drive
        for drive in drives:
            drive_id = drive.get('id')
            drive_name = drive.get('name', 'Unknown')
            
            print(f"\n[*] Crawling library: {drive_name}")
            print("-" * 70)
            
            files = self._crawl_folder_recursive(drive_id, drive_name)
            all_files.extend(files)
            
            print(f"[OK] Found {len(files)} files in {drive_name}")
        
        # Print summary
        duration = time.time() - start_time
        print("\n" + "=" * 70)
        print("CRAWLING COMPLETE")
        print("=" * 70)
        print(f"Total files found: {self.files_found}")
        print(f"Files to process: {len(all_files)}")
        print(f"Files skipped: {self.files_skipped}")
        print(f"Errors: {len(self.errors)}")
        print(f"Duration: {duration:.2f} seconds")
        
        if self.errors:
            print("\nErrors encountered:")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
        
        return all_files
    
    def download_file_batch(self, files_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Download a batch of files.
        
        Args:
            files_metadata: List of file metadata dictionaries
        
        Returns:
            List of metadata with 'local_path' added for successful downloads
        """
        print(f"\n[*] Downloading {len(files_metadata)} files...")
        
        downloaded_files = []
        
        for i, file_meta in enumerate(files_metadata, 1):
            file_name = file_meta['file_name']
            download_url = file_meta.get('download_url')
            
            if not download_url:
                print(f"[SKIP] No download URL for {file_name}")
                continue
            
            print(f"[{i}/{len(files_metadata)}] Downloading: {file_name}")
            
            local_path = self._download_file(download_url, file_name)
            
            if local_path:
                file_meta['local_path'] = local_path
                downloaded_files.append(file_meta)
        
        print(f"[OK] Successfully downloaded {len(downloaded_files)}/{len(files_metadata)} files")
        
        return downloaded_files


def get_sharepoint_crawler(site_url: str = None, auth_headers: Dict[str, str] = None) -> SharePointDocumentCrawler:
    """
    Get a configured SharePoint document crawler instance.
    
    Args:
        site_url: SharePoint site URL (uses env var if not provided)
        auth_headers: Authentication headers (uses sharepoint_auth if not provided)
    """
    if site_url is None:
        site_url = os.getenv('SHAREPOINT_SITE_URL', 'https://cloudfuzecom.sharepoint.com/sites/DOC360')
    
    if auth_headers is None:
        from app.sharepoint_auth import sharepoint_auth
        auth_headers = sharepoint_auth.get_headers()
    
    max_file_size_mb = int(os.getenv('SHAREPOINT_MAX_FILE_SIZE_MB', '50'))
    
    return SharePointDocumentCrawler(site_url, auth_headers, max_file_size_mb)

