# -*- coding: utf-8 -*-
"""
SharePoint Integration Test Script

Test the SharePoint integration without affecting the main vectorstore.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_sharepoint_auth():
    """Test SharePoint authentication."""
    print("=" * 60)
    print("SHAREPOINT AUTHENTICATION TEST")
    print("=" * 60)
    
    try:
        from app.sharepoint_auth import sharepoint_auth
        
        print("1. Testing SharePoint authentication...")
        if sharepoint_auth.test_connection():
            print("✅ SharePoint authentication successful!")
            return True
        else:
            print("❌ SharePoint authentication failed!")
            return False
            
    except Exception as e:
        print(f"❌ SharePoint authentication error: {e}")
        return False

def test_sharepoint_processor():
    """Test SharePoint content processing."""
    print("\n" + "=" * 60)
    print("SHAREPOINT CONTENT PROCESSING TEST")
    print("=" * 60)
    
    try:
        from app.sharepoint_processor import SharePointProcessor
        
        print("1. Initializing SharePoint processor...")
        processor = SharePointProcessor()
        
        print("2. Testing page content extraction...")
        # Test with a simple page URL
        test_url = "https://cloudfuzecom.sharepoint.com/sites/DOC360/SitePages/Multi%20User%20Golden%20Image%20Combinations.aspx"
        
        page_data = processor.get_page_content(test_url)
        if page_data:
            print("✅ Page content extraction successful!")
            print(f"   Page title: {page_data.get('title', 'Unknown')}")
            return True
        else:
            print("❌ Page content extraction failed!")
            return False
            
    except Exception as e:
        print(f"❌ SharePoint processing error: {e}")
        return False

def test_environment_variables():
    """Test required environment variables."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT VARIABLES TEST")
    print("=" * 60)
    
    required_vars = [
        "MICROSOFT_CLIENT_ID",
        "MICROSOFT_CLIENT_SECRET", 
        "MICROSOFT_TENANT",
        "SHAREPOINT_SITE_URL",
        "SHAREPOINT_START_PAGE"
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Hide secret values
            display_value = value[:20] + "..." if "SECRET" in var else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_good = False
    
    return all_good

def main():
    """Run all SharePoint integration tests."""
    print("🚀 SharePoint Integration Test Suite")
    print("=" * 60)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    if not env_ok:
        print("\n❌ Environment variables test failed!")
        print("Please set the required environment variables in your .env file")
        return
    
    # Test authentication
    auth_ok = test_sharepoint_auth()
    
    if not auth_ok:
        print("\n❌ Authentication test failed!")
        print("Please check your Microsoft app registration permissions")
        return
    
    # Test content processing
    processor_ok = test_sharepoint_processor()
    
    if not processor_ok:
        print("\n❌ Content processing test failed!")
        print("Please check SharePoint site access and URL configuration")
        return
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("SharePoint integration is ready to use!")
    print("\nTo enable SharePoint in your vectorstore:")
    print("1. Set ENABLE_SHAREPOINT_SOURCE=true in your .env file")
    print("2. Set INITIALIZE_VECTORSTORE=true to rebuild vectorstore")
    print("3. Restart your application")

if __name__ == "__main__":
    main()
