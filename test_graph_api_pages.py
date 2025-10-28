# -*- coding: utf-8 -*-
"""
Test Microsoft Graph API for SharePoint Pages
"""

from dotenv import load_dotenv
import os
import requests

load_dotenv()

def test_graph_api_for_pages():
    """Test using Microsoft Graph API to get SharePoint page content."""
    
    from app.sharepoint_auth import sharepoint_auth
    
    print("=" * 60)
    print("TESTING MICROSOFT GRAPH API FOR SHAREPOINT PAGES")
    print("=" * 60)
    
    # Get access token
    headers = sharepoint_auth.get_headers()
    
    # Get site info
    site_url = os.getenv("SHAREPOINT_SITE_URL")
    from urllib.parse import urlparse
    parsed = urlparse(site_url)
    hostname = parsed.netloc
    site_path = parsed.path
    
    graph_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
    
    print(f"\n[*] Getting site info: {graph_url}")
    
    response = requests.get(graph_url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        site_data = response.json()
        site_id = site_data.get('id')
        print(f"✅ Site found: {site_data.get('name')}")
        print(f"   Site ID: {site_id[:50]}...")
        
        # Try to get pages
        pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages"
        print(f"\n[*] Getting pages: {pages_url}")
        
        pages_response = requests.get(pages_url, headers=headers, timeout=30)
        
        if pages_response.status_code == 200:
            pages_data = pages_response.json()
            pages = pages_data.get('value', [])
            print(f"✅ Found {len(pages)} pages!")
            
            for i, page in enumerate(pages[:5], 1):
                print(f"\n   Page {i}:")
                print(f"      Name: {page.get('name')}")
                print(f"      Title: {page.get('title')}")
                print(f"      Web URL: {page.get('webUrl')}")
            
            # Try to get content for one page
            if pages:
                first_page = pages[0]
                page_id = first_page.get('id')
                print(f"\n[*] Getting content for page: {page_id}")
                
                # Get page content
                content_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}"
                content_response = requests.get(content_url, headers=headers, timeout=30)
                
                if content_response.status_code == 200:
                    content_data = content_response.json()
                    print(f"✅ Got page content!")
                    print(f"   Title: {content_data.get('title')}")
                    print(f"   Content type: {content_data.get('contentType')}")
                    print(f"   Layout: {content_data.get('layout')}")
                    
                    # Try to get web parts (actual content)
                    webparts_url = f"{content_url}/webParts"
                    webparts_response = requests.get(webparts_url, headers=headers, timeout=30)
                    
                    if webparts_response.status_code == 200:
                        webparts_data = webparts_response.json()
                        print(f"✅ Got {len(webparts_data.get('value', []))} web parts!")
                        
                        for i, webpart in enumerate(webparts_data.get('value', [])[:3], 1):
                            print(f"\n   WebPart {i}:")
                            print(f"      Type: {webpart.get('webPartType')}")
                            print(f"      Data: {str(webpart.get('data', {}))[:100]}...")
                        
                        return True
                    else:
                        print(f"⚠️  Web parts request failed: {webparts_response.status_code}")
                        return False
                else:
                    print(f"❌ Failed to get page content: {content_response.status_code}")
                    return False
            else:
                print("❌ No pages found")
                return False
        else:
            print(f"❌ Failed to get pages: {pages_response.status_code}")
            print(f"   Response: {pages_response.text}")
            return False
    else:
        print(f"❌ Failed to get site: {response.status_code}")
        return False

if __name__ == "__main__":
    test_graph_api_for_pages()
