# -*- coding: utf-8 -*-
"""
Detailed Test for SharePoint Page Content Access
"""

from dotenv import load_dotenv
import os
import requests

load_dotenv()

from app.sharepoint_auth import sharepoint_auth

def test_detailed_page_access():
    """Test different methods to access SharePoint page content."""
    
    print("=" * 60)
    print("DETAILED SHAREPOINT PAGE CONTENT ACCESS TEST")
    print("=" * 60)
    
    headers = sharepoint_auth.get_headers()
    
    # Get site
    site_url = os.getenv("SHAREPOINT_SITE_URL")
    from urllib.parse import urlparse
    parsed = urlparse(site_url)
    hostname = parsed.netloc
    site_path = parsed.path
    
    graph_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
    
    print(f"[*] Getting site info...")
    response = requests.get(graph_url, headers=headers, timeout=30)
    site_data = response.json()
    site_id = site_data.get('id')
    
    print(f"✅ Site ID: {site_id}")
    
    # Get pages
    pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages"
    pages_response = requests.get(pages_url, headers=headers, timeout=30)
    pages = pages_response.json().get('value', [])
    
    if not pages:
        print("❌ No pages found")
        return
    
    # Test with first page
    page = pages[0]
    page_id = page.get('id')
    page_title = page.get('title')
    page_url = page.get('webUrl')
    
    print(f"\n[*] Testing with page: {page_title}")
    print(f"   Page ID: {page_id}")
    print(f"   URL: {page_url}")
    
    # Method 1: Get page content endpoint
    print(f"\n[Method 1] Trying /content endpoint...")
    content_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}/content"
    try:
        content_response = requests.get(content_url, headers=headers, timeout=30)
        print(f"   Status: {content_response.status_code}")
        if content_response.status_code == 200:
            print(f"   ✅ Success! Got {len(content_response.text)} bytes")
            print(f"   Preview: {content_response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Method 2: Try to parse the page URL to get file info
    print(f"\n[Method 2] Trying to get page as drive item...")
    # Parse page URL to get drive and item ID
    from urllib.parse import unquote
    page_path_encoded = page_url.split('SitePages/')[1] if 'SitePages/' in page_url else ''
    page_path = unquote(page_path_encoded)
    
    print(f"   Page path: {page_path}")
    
    # Try to get from drive
    drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    drives_response = requests.get(drives_url, headers=headers, timeout=30)
    
    if drives_response.status_code == 200:
        drives_data = drives_response.json()
        drives = drives_data.get('value', [])
        print(f"   Found {len(drives)} drives")
        
        # Find the documents library (usually drive with name 'Documents')
        for drive in drives:
            drive_name = drive.get('name')
            print(f"   Drive: {drive_name}")
            
            if drive_name == 'Documents':
                drive_id = drive.get('id')
                
                # Try to get the page file from drive
                # SitePages items are in a folder
                items_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children"
                items_response = requests.get(items_url, headers=headers, timeout=30)
                
                if items_response.status_code == 200:
                    items_data = items_response.json()
                    items = items_data.get('value', [])
                    print(f"   Found {len(items)} items in root")
                    
                    # Find SitePages folder
                    for item in items:
                        item_name = item.get('name')
                        print(f"   Item: {item_name}")
                        
                    # Check if item is a folder
                    if item.get('folder'):
                        folder_id = item.get('id')
                        folder_name = item.get('name')
                        print(f"   Folder: {folder_name}")
                        
                        # Check all folders for SitePages
                        folder_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{folder_id}/children"
                        folder_response = requests.get(folder_url, headers=headers, timeout=30)
                        
                        if folder_response.status_code == 200:
                            folder_data = folder_response.json()
                            sub_items = folder_data.get('value', [])
                            
                            for sub_item in sub_items:
                                sub_item_name = sub_item.get('name')
                                print(f"      Sub item: {sub_item_name}")
                                
                                if sub_item_name and 'SitePages' in sub_item_name:
                                    site_pages_id = sub_item.get('id')
                                    print(f"\n      ✅ Found SitePages in {folder_name}")
                                    
                                    # Get files in SitePages
                                    site_pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{site_pages_id}/children"
                                    site_pages_response = requests.get(site_pages_url, headers=headers, timeout=30)
                                    
                                    if site_pages_response.status_code == 200:
                                        site_pages_data = site_pages_response.json()
                                        site_page_files = site_pages_data.get('value', [])
                                        print(f"         Found {len(site_page_files)} files")
                                        
                                        for file in site_page_files:
                                            file_name = file.get('name')
                                            print(f"         File: {file_name}")
                                            
                                            if file.get('name') == page_path:
                                                file_id = file.get('id')
                                                print(f"         ✅ Found our page!")
                                                print(f"         File ID: {file_id}")
                                                
                                                # Try to get content
                                                content_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{file_id}/content"
                                                file_content_response = requests.get(content_url, headers=headers, timeout=30)
                                                
                                                if file_content_response.status_code == 200:
                                                    print(f"         ✅ GOT CONTENT! ({len(file_content_response.content)} bytes)")
                                                    print(f"         First 500 chars: {file_content_response.text[:500]}")
                                                    return file_content_response.text
                                                else:
                                                    print(f"         Status: {file_content_response.status_code}")
    
    print("\n[Method 3] Trying SharePoint REST API...")
    # SharePoint REST API approach
    rest_url = f"{site_url}/_api/web/getfilebyserverrelativeurl('{site_path}/SitePages/{page_path}')/\$value"
    print(f"   Trying: {rest_url}")
    
    # This won't work without proper SharePoint REST API authentication
    print("   ⚠️  SharePoint REST API requires different authentication")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)
    print("The most reliable way is to use SharePoint REST API")
    print("which requires adding 'Sites.Selected' permission")
    print("or implementing SharePoint-specific authentication.")

if __name__ == "__main__":
    test_detailed_page_access()
