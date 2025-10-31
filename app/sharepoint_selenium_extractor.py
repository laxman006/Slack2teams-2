# -*- coding: utf-8 -*-
"""
SharePoint Selenium-Based Content Extractor

Uses Selenium browser automation to extract SharePoint page content.
This is the most reliable automated approach.
"""

import os
import time
from typing import List, Optional, Set
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from langchain_core.documents import Document

# Import Selenium components
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class SharePointSeleniumExtractor:
    """Extract SharePoint content using Selenium browser automation."""
    
    def __init__(self):
        self.site_url = os.getenv("SHAREPOINT_SITE_URL", "https://cloudfuzecom.sharepoint.com/sites/DOC360")
        self.start_page = os.getenv("SHAREPOINT_START_PAGE", "/SitePages/Multi%20User%20Golden%20Image%20Combinations.aspx")
        self.max_depth = int(os.getenv("SHAREPOINT_MAX_DEPTH", "3"))
        self.crawled_urls: Set[str] = set()
        
        print(f"[*] SharePoint Selenium Extractor initialized")
        print(f"   Site: {self.site_url}")
    
    def setup_driver(self):
        """Setup Chrome WebDriver with options."""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not installed. Run: pip install selenium webdriver-manager")
        
        chrome_options = Options()
        
        # Run in visible mode (not headless) so user can see and interact
        # chrome_options.add_argument('--headless')  # Commented out for user interaction
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Try to use webdriver-manager for automatic ChromeDriver
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("[OK] Chrome WebDriver initialized with webdriver-manager")
        except Exception as e:
            print(f"[INFO] webdriver-manager failed: {e}")
            # Fallback to system ChromeDriver
            driver = webdriver.Chrome(options=chrome_options)
            print("[OK] Chrome WebDriver initialized")
        
        return driver
    
    def extract_page_content(self, driver) -> str:
        """Extract content from current page."""
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # SharePoint Modern Page - Try multiple selectors for content area
        main_content = None
        
        # Priority 1: Modern SharePoint page content canvas
        main_content = soup.find('div', {'class': lambda x: x and 'CanvasZone' in x})
        
        if not main_content:
            # Priority 2: Page content wrapper
            main_content = soup.find('div', {'data-automation-id': 'contentScrollRegion'})
        
        if not main_content:
            # Priority 3: Main canvas section
            main_content = soup.find('div', {'class': lambda x: x and 'mainContent' in x})
        
        if not main_content:
            # Priority 4: Try to find the canvas element
            main_content = soup.find('div', {'role': 'main'})
        
        if not main_content:
            # Priority 5: Look for the article element
            main_content = soup.find('article')
        
        if not main_content:
            # Fallback: Get the body but remove navigation
            main_content = soup.find('body')
            if main_content:
                # Remove SharePoint chrome elements
                for unwanted in main_content.select('[class*="ribbon"], [class*="navigation"], [class*="commandBar"], [class*="nav-"], nav, header'):
                    unwanted.decompose()
        
        if main_content:
            # Remove unwanted elements
            for script in main_content(["script", "style", "nav", "header", "footer", "button"]):
                script.decompose()
            
            # Remove specific SharePoint UI elements
            for element in main_content.select('[class*="CommandBar"], [class*="Ribbon"], [class*="SuiteNav"]'):
                element.decompose()
            
            # Get text content
            text_content = main_content.get_text(separator='\n', strip=True)
            
            # Clean up - remove common SharePoint UI text
            skip_phrases = [
                'Skip Ribbon Commands',
                'Skip to main content',
                'Turn on more accessible mode',
                'Turn off more accessible mode',
                'enable scripts and reload',
                'secured browser on the server',
                'To navigate through the Ribbon',
                'Sign in',
                'Laxman Kadari'  # User-specific
            ]
            
            lines = []
            for line in text_content.splitlines():
                line = line.strip()
                # Skip empty lines and SharePoint UI text
                if line and not any(phrase in line for phrase in skip_phrases):
                    lines.append(line)
            
            cleaned_content = '\n'.join(lines)
            
            # If content is too short (likely failed extraction), return empty
            if len(cleaned_content) < 100:
                print(f"[WARNING] Extracted content too short ({len(cleaned_content)} chars), likely incomplete")
                return ""
            
            return cleaned_content
        
        return ""
    
    def find_sharepoint_links(self, driver) -> List[str]:
        """Find all SharePoint page links on current page."""
        try:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                # Look for SitePages links
                if 'SitePages' in href:
                    # Extract the path component
                    if href.startswith('/'):
                        links.append(href)
                    elif 'sharepoint.com' in href:
                        # Extract just the path from full URL
                        from urllib.parse import urlparse
                        parsed = urlparse(href)
                        links.append(parsed.path)
            
            # Remove duplicates
            return list(set(links))
        except Exception as e:
            print(f"[ERROR] Failed to find links: {e}")
            return []
    
    def extract_all_pages(self) -> List[Document]:
        """Extract content from all SharePoint pages."""
        print("=" * 60)
        print("SHAREPOINT SELENIUM CONTENT EXTRACTION")
        print("=" * 60)
        
        if not SELENIUM_AVAILABLE:
            print("[ERROR] Selenium not available")
            print("[INFO] Install with: pip install selenium webdriver-manager")
            return []
        
        all_documents = []
        driver = None
        
        try:
            # Setup driver
            driver = self.setup_driver()
            
            # Navigate to SharePoint
            full_url = f"{self.site_url}{self.start_page}"
            print(f"[*] Navigating to: {full_url}")
            driver.get(full_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if we need authentication
            current_url = driver.current_url
            if "login.microsoftonline.com" in current_url or "signin" in current_url:
                print("\n" + "=" * 60)
                print("⚠️  AUTHENTICATION REQUIRED!")
                print("=" * 60)
                print("📌 ACTION NEEDED:")
                print("   1. Look for the Chrome browser window that just opened")
                print("   2. Sign in to your SharePoint account")
                print("   3. Wait for the page to fully load")
                print("   4. Return here - the script will continue automatically")
                print(f"\n⏱️  Waiting up to 5 minutes for authentication...")
                print("=" * 60 + "\n")
                
                # Wait for authentication (max 5 minutes)
                wait_time = 0
                while ("login" in driver.current_url.lower() or "signin" in driver.current_url.lower()) and wait_time < 300:
                    time.sleep(2)
                    wait_time += 2
                    if wait_time % 30 == 0:
                        print(f"   Still waiting... ({wait_time // 60} min {wait_time % 60} sec)")
                    driver.switch_to.window(driver.window_handles[0])
                
                if "login" in driver.current_url.lower() or "signin" in driver.current_url.lower():
                    print("\n[ERROR] Authentication timeout - please sign in faster next time")
                    return []
                else:
                    print("\n✅ Authentication successful!")
            
            print("[OK] Ready to extract content")
            
            # Start with the current page
            all_urls = [driver.current_url]
            depth = 0
            
            while depth <= self.max_depth and len(all_urls) > 0:
                current_batch = list(all_urls)
                all_urls = []
                
                print(f"\n[*] Depth {depth}: Processing {len(current_batch)} pages")
                
                for url in current_batch:
                    if url in self.crawled_urls:
                        continue
                    
                    try:
                        print(f"   Crawling: {url}")
                        driver.get(url)
                        time.sleep(2)  # Wait for page load
                        
                        # Extract content
                        page_title = driver.title
                        content = self.extract_page_content(driver)
                        
                        if content:
                            doc = Document(
                                page_content=content[:15000],
                                metadata={
                                    "source_type": "sharepoint",
                                    "source": "cloudfuze_doc360",
                                    "page_title": page_title,
                                    "page_url": url,
                                    "content_type": "sharepoint_page",
                                    "depth": depth
                                }
                            )
                            all_documents.append(doc)
                            print(f"   ✅ Extracted ({len(content)} chars)")
                        
                        self.crawled_urls.add(url)
                        
                        # Find links for next depth
                        if depth < self.max_depth:
                            links = self.find_sharepoint_links(driver)
                            # Make sure links are absolute URLs and filter out already crawled
                            links = [urljoin(url, link) if not link.startswith('http') else link for link in links]
                            links = [link for link in links if link not in self.crawled_urls]
                            all_urls.extend(links)  # Get ALL links, not just 5
                        
                    except Exception as e:
                        print(f"   ⚠️ Error: {e}")
                        continue
                
                depth += 1
            
            print(f"\n[OK] Extraction complete!")
            print(f"   Pages crawled: {len(self.crawled_urls)}")
            print(f"   Documents created: {len(all_documents)}")
            
            return all_documents
            
        except Exception as e:
            print(f"[ERROR] Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        finally:
            if driver:
                print("[*] Closing browser...")
                driver.quit()
                print("[OK] Browser closed")


def extract_sharepoint_pages() -> List[Document]:
    """Main function for automated extraction."""
    extractor = SharePointSeleniumExtractor()
    return extractor.extract_all_pages()

if __name__ == "__main__":
    docs = extract_sharepoint_pages()
    print(f"\n📄 Total documents: {len(docs)}")
    
    for doc in docs:
        print(f"\n   - {doc.metadata.get('page_title')}: {len(doc.page_content)} chars")
