# -*- coding: utf-8 -*-
"""
Test Selenium-based SharePoint extraction
"""

from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 60)
print("SELENIUM-BASED SHAREPOINT EXTRACTION TEST")
print("=" * 60)

print("\nThis will:")
print("1. Open a Chrome browser window")
print("2. Navigate to SharePoint DOC360 site")
print("3. Ask you to authenticate (if needed)")
print("4. Extract all page content automatically")
print("5. Close the browser when done")
print()

response = input("Ready to start? (y/n): ")

if response.lower() != 'y':
    print("Cancelled.")
    exit()

try:
    from app.sharepoint_selenium_extractor import extract_sharepoint_pages
    
    print("\n[*] Starting Selenium-based extraction...")
    print("[*] A Chrome window will open - please wait...\n")
    
    docs = extract_sharepoint_pages()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if docs:
        print(f"✅ Extracted {len(docs)} documents\n")
        
        for i, doc in enumerate(docs, 1):
            print(f"\n   Document {i}:")
            print(f"      Title: {doc.metadata.get('page_title')}")
            print(f"      URL: {doc.metadata.get('page_url')}")
            print(f"      Length: {len(doc.page_content)} characters")
            print(f"      Preview: {doc.page_content[:200]}...")
        
        print("\n✅ SUCCESS! SharePoint content extracted!")
        print("\n💡 Next steps:")
        print("1. Review the extracted content above")
        print("2. If good, set ENABLE_SHAREPOINT_SOURCE=true in .env")
        print("3. Run: python server.py")
        print("4. SharePoint content will be added to vectorstore")
    else:
        print("❌ No documents extracted")
        print("\n[INFO] This might be due to:")
        print("   - Authentication timeout")
        print("   - No pages found")
        print("   - Selenium setup issues")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nRun this command to install:")
    print("   pip install selenium webdriver-manager")
    print("\nOr run:")
    if os.name == 'nt':
        print("   .\\setup_selenium.bat")
    else:
        print("   ./setup_selenium.sh")

