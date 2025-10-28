# -*- coding: utf-8 -*-
"""
Test SharePoint Files API to Get Page Content
"""

from dotenv import load_dotenv
import os
import requests

load_dotenv()
from app.sharepoint_auth import sharepoint_auth

def test_files_api():
    """Test using SharePoint Files API to get page files."""
    
    print("=" * 60)
    print("TESTING SHAREPOINT FILES API")
    print("=" * 60)
    
    headers = sharepoint_auth.get_headers()
    
    # Get site
    site_url = os.getenv("SHAREPOINT_SITE_URL")
    from urllib.parse import urlparse
    parsed = urlparse(site_url)
    hostname = parsed.netloc
    site_path = parsed.path
    
    graph_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
    
    print(f"[*] Getting site...")
    response = requests.get(graph_url, headers=headers, timeout=30)
    site_data = response.json()
    site_id = site_data.get('id')
    
    print(f"✅ Site ID: {site_id[:50]}...")
    
    # Get drives
    drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    print(f"[*] Getting drives...")
    drives_response = requests.get(drives_url, headers=headers, timeout=30)
    drives = drives_response.json().get('value', [])
    
    print(f"✅ Found {len(drives)} drives")
    
    # Look for SitePages files in all drives
    for drive in drives:
        drive_id = drive.get('id')
        drive_name = drive.get('name')
        
        print(f"\n[*] Checking drive: {drive_name}")
        
        # Search for files with "aspx" extension
        search_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/search(q='.aspx')"
        search_response = requests.get(search_url, headers=headers, timeout=30)
        
        if search_response.status_code == 200:
            search_results = search_response.json().get('value', [])
            print(f"   Found {len(search_results)} .aspx files")
            
            for result in search_results:
                file_name = result.get('name')
                file_id = result.get('id')
                print(f"      File: {file_name}")
                
                # Try to get file content
                if '.aspx' in file_name.lower():
                    content_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{file_id}/content"
                    print(f"      [*] Trying to get content...")
                    
                    content_response = requests.get(content_url, headers=headers, timeout=30)
                    
                    if content_response.status_code == 200:
                        content = content_response.text
                        print(f"      ✅ GOT CONTENT! ({len(content)} bytes)")
                        print(f"      Preview: {content[:200]}...")
                        return content
                    else:
                        print(f"      ❌ Status: {content_response.status_code}")
        else:
            print(f"   Search failed: {search_response.status_code}")
    
    return None

if __name__ == "__main__":
    content = test_files_api()
    if content:
        print("\n✅ SUCCESS! This method works!")
    else:
        print("\n❌ Could not get content")
        print("\n💡 SharePoint pages are special - they're not regular files")
        print("   They require special API endpoints or authenticated browser access")
