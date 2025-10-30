# -*- coding: utf-8 -*-
"""
SharePoint Selenium-Based Content Extractor

Uses Selenium browser automation to extract SharePoint page content.
This is the most reliable automated approach.
"""

import os
import time
from typing import List, Optional, Set
from urllib.parse import urljoin, unquote
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
    from selenium.webdriver.common.action_chains import ActionChains
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class SharePointSeleniumExtractor:
    """Extract SharePoint content using Selenium browser automation."""
    
    def __init__(self):
        self.site_url = os.getenv("SHAREPOINT_SITE_URL", "https://cloudfuzecom.sharepoint.com/sites/DOC360")
        self.start_page = os.getenv("SHAREPOINT_START_PAGE", "")
        # Set max_depth very high for unlimited depth (extract all folders)
        self.max_depth = int(os.getenv("SHAREPOINT_MAX_DEPTH", "999"))
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
        # Keep browser open after script ends (helps with debugging)
        chrome_options.add_experimental_option("detach", True)
        
        try:
            print("[*] Attempting to create Chrome WebDriver...")
            # Try to use webdriver-manager for automatic ChromeDriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                print("[*] Using webdriver-manager for ChromeDriver...")
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("[OK] Chrome WebDriver initialized with webdriver-manager")
            except Exception as e:
                print(f"[INFO] webdriver-manager failed: {e}")
                print("[*] Trying system ChromeDriver...")
                # Fallback to system ChromeDriver
                driver = webdriver.Chrome(options=chrome_options)
                print("[OK] Chrome WebDriver initialized with system ChromeDriver")
            
            # Verify driver is working
            print("[*] Verifying driver...")
            driver.get("about:blank")
            print(f"[OK] Driver verified - can navigate. Window handle: {driver.current_window_handle if hasattr(driver, 'current_window_handle') else 'N/A'}")
            
            return driver
        except Exception as e:
            print(f"[ERROR] Failed to create Chrome WebDriver: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def extract_page_content(self, driver) -> str:
        """Extract content from current page."""
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Try to find main content area
        main_content = (
            soup.find('main') or 
            soup.find('div', {'id': 'spPageContent'}) or
            soup.find('div', {'class': 'ms-CommandBar'}) or
            soup.find('body')
        )
        
        if main_content:
            # Remove scripts and styles
            for script in main_content(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Get text content
            text_content = main_content.get_text(separator='\n', strip=True)
            
            # Clean up
            lines = [line.strip() for line in text_content.splitlines() if line.strip()]
            return '\n'.join(lines)
        
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
        """Extract content from all SharePoint Documents library (folders and files)."""
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
            print("[*] Setting up Chrome WebDriver...")
            driver = self.setup_driver()
            print(f"[OK] Driver created: {driver}")
            print(f"[INFO] Driver session ID: {driver.session_id if hasattr(driver, 'session_id') else 'N/A'}")
            
            # Navigate to SharePoint Documents library
            # If start_page is empty or just "/", go to Documents library
            if not self.start_page or self.start_page == "/" or self.start_page.strip() == "":
                # Navigate to Documents library
                documents_url = f"{self.site_url}/Shared Documents/Forms/AllItems.aspx"
                print(f"[*] Navigating to Documents library: {documents_url}")
                driver.get(documents_url)
                print(f"[INFO] Current URL after navigation: {driver.current_url}")
            else:
                # Use specified start page (for backward compatibility)
                full_url = f"{self.site_url}{self.start_page}"
                print(f"[*] Navigating to: {full_url}")
                driver.get(full_url)
                print(f"[INFO] Current URL after navigation: {driver.current_url}")
            
            # Wait for page to load
            print("[*] Waiting for page to load...")
            time.sleep(3)
            
            # Check if we need authentication
            current_url = driver.current_url
            print(f"[INFO] Current URL: {current_url}")
            print(f"[INFO] Title: {driver.title}")
            
            if "login.microsoftonline.com" in current_url or "signin" in current_url or "login" in current_url.lower():
                print("[WARNING] Authentication required!")
                print("[INFO] Please sign in to SharePoint in the browser window")
                print("[INFO] The browser window should be visible")
                print("[INFO] Waiting for authentication (max 3 minutes)...")
                
                # Wait for authentication (max 3 minutes - increased from 2)
                wait_time = 0
                while ("login" in driver.current_url.lower() or "signin" in driver.current_url.lower()) and wait_time < 180:
                    time.sleep(3)
                    wait_time += 3
                    try:
                        driver.switch_to.window(driver.window_handles[0])
                        current_url = driver.current_url
                        print(f"   [WAIT] Still on login page... ({wait_time}s/{180}s)")
                    except:
                        print(f"   [WAIT] Window may have changed... ({wait_time}s/{180}s)")
                
                current_url = driver.current_url
                if "login" in current_url.lower() or "signin" in current_url.lower():
                    print(f"[ERROR] Authentication timeout after {wait_time} seconds")
                    print(f"[ERROR] Final URL: {current_url}")
                    print(f"[ERROR] Browser will stay open for 60 seconds for debugging")
                    time.sleep(60)
                    return []
            
            print(f"[OK] Ready to extract content from: {driver.current_url}")
            
            # If start_page is empty, extract from Documents library recursively
            if not self.start_page or self.start_page == "/" or self.start_page.strip() == "":
                # Ensure we're on Documents library page (sometimes auth redirects us)
                documents_url = f"{self.site_url}/Shared Documents/Forms/AllItems.aspx"
                current = driver.current_url
                if "AllItems.aspx" not in current and "Shared Documents" not in current:
                    print(f"[INFO] Re-navigating to Documents library (was on: {current})")
                    driver.get(documents_url)
                    time.sleep(5)  # Wait for page load
                    
                    # Check if we need authentication again (might redirect after re-nav)
                    if "login.microsoftonline.com" in driver.current_url or "signin" in driver.current_url:
                        print("[INFO] Need to authenticate again - waiting...")
                        wait_time = 0
                        while ("login" in driver.current_url.lower() or "signin" in driver.current_url.lower()) and wait_time < 120:
                            time.sleep(2)
                            wait_time += 2
                            driver.switch_to.window(driver.window_handles[0])
                
                # Extract from Documents library (folders and files)
                all_documents = self.extract_from_documents_library(driver, folder_path=[])
            else:
                # Original page-by-page extraction (for backward compatibility)
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
                                print(f"   [OK] Extracted ({len(content)} chars)")
                            
                            self.crawled_urls.add(url)
                            
                            # Find links for next depth
                            if depth < self.max_depth:
                                links = self.find_sharepoint_links(driver)
                                # Make sure links are absolute URLs and filter out already crawled
                                links = [urljoin(url, link) if not link.startswith('http') else link for link in links]
                                links = [link for link in links if link not in self.crawled_urls]
                                all_urls.extend(links)  # Get ALL links, not just 5
                            
                        except Exception as e:
                            print(f"   [ERROR] Error: {e}")
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
            # Don't close driver on error - let user see what happened
            if driver:
                print("[WARNING] Browser will stay open for debugging. Close manually or wait for timeout.")
                # Keep browser open for at least 30 seconds so user can see what happened
                time.sleep(30)
            return []
        
        finally:
            if driver:
                print("[*] Closing browser...")
                try:
                    driver.quit()
                    print("[OK] Browser closed")
                except Exception as e:
                    print(f"[WARNING] Error closing browser: {e}")
    
    def extract_file_content(self, driver, file_url: str, file_name: str) -> Optional[str]:
        """Extract text content from a file (PDF, Word, Excel, etc.)."""
        try:
            # Navigate to file view/download page
            driver.get(file_url)
            time.sleep(3)
            
            # Try to extract text from the page
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Clean up
            lines = [line.strip() for line in text_content.splitlines() if line.strip()]
            content = '\n'.join(lines)
            
            # For Office files, SharePoint might show preview text
            # For PDFs, we might need to click "View" or "Download" to see content
            return content if len(content) > 100 else None  # Only return if substantial content
            
        except Exception as e:
            print(f"      [WARNING] Could not extract content from {file_name}: {e}")
            return None
    
    def navigate_back_in_sharepoint(self, driver):
        """Navigate back in SharePoint using breadcrumb navigation (not browser back)."""
        try:
            # Try to find and click breadcrumb link
            # SharePoint breadcrumbs are typically in a nav element
            breadcrumb_selectors = [
                "span[aria-label*='Navigate up']",
                "button[aria-label*='Navigate up']",
                "a[aria-label*='Navigate up']",
                ".ms-Breadcrumb-listItem a",  # SharePoint breadcrumb links
                ".ms-Breadcrumb a",  # Breadcrumb anchor
                "[data-automation-id='BreadcrumbItem'] a",  # Modern UI breadcrumb
                "button[aria-label*='Back']",  # Back button
                "a[aria-label*='Back']",  # Back link
            ]
            
            for selector in breadcrumb_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Click the second-to-last or parent breadcrumb to go back
                        back_element = elements[-2] if len(elements) > 1 else elements[0]
                        ActionChains(driver).move_to_element(back_element).click().perform()
                        time.sleep(3)
                        print("   [OK] Navigated back via breadcrumb")
                        return True
                except:
                    continue
            
            # Fallback: Try finding "Documents" or parent folder link in breadcrumb
            try:
                # Look for Documents link or parent folder
                breadcrumb_links = driver.find_elements(By.CSS_SELECTOR, ".ms-Breadcrumb a, [data-automation-id='BreadcrumbItem'] a")
                for link in breadcrumb_links:
                    link_text = link.text.strip()
                    if "Document" in link_text or link == breadcrumb_links[-2] if len(breadcrumb_links) > 1 else False:
                        ActionChains(driver).move_to_element(link).click().perform()
                        time.sleep(3)
                        print("   [OK] Navigated back via breadcrumb link")
                        return True
            except:
                pass
            
            # Final fallback: Try finding Documents link on page
            try:
                doc_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Documents")
                ActionChains(driver).move_to_element(doc_link).click().perform()
                time.sleep(3)
                print("   [OK] Navigated back to Documents")
                return True
            except:
                pass
            
            print("   [WARNING] Could not find breadcrumb navigation - may need manual navigation")
            return False
        except Exception as e:
            print(f"   [ERROR] Error navigating back: {e}")
            return False
    
    def extract_from_documents_library(self, driver, current_url: str = None, visited_urls: Set[str] = None, depth: int = 0, folder_path: List[str] = None) -> List[Document]:
        """Recursively extract documents from SharePoint Documents library using double-click navigation."""
        if visited_urls is None:
            visited_urls = set()
        
        if folder_path is None:
            folder_path = []
        
        # Use folder path as key (more reliable than URL)
        folder_key = " > ".join(folder_path) if folder_path else "Documents"
        if folder_key in visited_urls:
            print(f"   [SKIP] Already visited: {folder_key}")
            return []
        
        visited_urls.add(folder_key)
        if current_url:
            visited_urls.add(current_url)
        all_documents = []
        
        try:
            print(f"\n[*] Depth {depth}: Exploring folder: {folder_key}")
            
            # For root folder, navigate to Documents library
            if depth == 0:
                if current_url is None or ("AllItems.aspx" not in current_url and "Shared Documents" not in current_url):
                    documents_url = f"{self.site_url}/Shared Documents/Forms/AllItems.aspx"
                    print(f"[INFO] Navigating to Documents library: {documents_url}")
                    driver.get(documents_url)
                    time.sleep(5)
                    current_url = driver.current_url
            # For subfolders, we should already be here via double-click, just wait
            else:
                time.sleep(3)  # Wait for page to load after double-click
            
            # Scroll multiple times to load all items (SharePoint uses lazy loading)
            for _ in range(5):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Verify we're on a valid SharePoint folder/library page
            actual_url = driver.current_url
            page_title = driver.title
            
            # Check if we're on a valid page (not redirected to login/default page)
            if "_forms/default.aspx" in actual_url or "login" in actual_url.lower() or "signin" in actual_url.lower():
                print(f"   [ERROR] Got redirected to invalid page: {actual_url}")
                print(f"   [INFO] Skipping this folder (likely authentication issue)")
                return []
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract folder structure and file names
            folder_content_text = self.extract_page_content(driver)
            
            # Determine current folder name
            # If folder_path is provided (from parent), use it
            # Otherwise, determine from URL or title
            if folder_path:
                # We're in a subfolder - folder_path already has the path
                current_folder_path = folder_path.copy()
                # Get current folder name from URL or title
                folder_name = driver.title or "Unknown Folder"
                # Try to get folder name from URL
                if current_url:
                    url_parts = current_url.split('/')
                    for part in reversed(url_parts):
                        decoded = unquote(part)
                        if decoded and decoded not in ['Forms', 'AllItems.aspx', 'View.aspx', 'Shared Documents', 'Documents'] and len(decoded) > 2:
                            folder_name = decoded
                            break
                # Add current folder to path if not already there
                if len(current_folder_path) == 0 or current_folder_path[-1] != folder_name:
                    current_folder_path.append(folder_name)
            else:
                # Root Documents folder
                current_folder_path = ["Documents"]
                folder_name = "Documents"
            
            # Build tag: sharepoint/folder/subfolder/subsubfolder
            # Sanitize folder names (remove special chars that might break tag structure)
            sanitized_path = [f.replace('/', '-').replace('\\', '-').strip() for f in current_folder_path if f.strip()]
            tag = "/".join(["sharepoint"] + sanitized_path)
            
            # Find all files and folders
            base_url = current_url.rsplit('/', 1)[0] if '/' in current_url else current_url
            folder_links = []
            file_links = []
            
            # File extensions to extract (documents and videos)
            file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.rtf', '.mp4', '.avi', '.mov', '.wmv', '.mkv']
            
            # Try multiple strategies to find files and folders
            # Strategy 1: Find all links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                
                if not link_text or len(link_text) < 1:
                    continue
                
                # Skip UI elements and navigation links
                ui_elements = ['view', 'edit', 'share', 'download', 'more', 'open', 'name', 'modified', 'type', 'size', 'sort', 'filter', 
                              'return to classic sharepoint', 'classic sharepoint', 'switch view', 'new', 'upload', 'sync', 
                              'refresh', 'close', 'back', 'previous', 'next', 'first', 'last']
                if link_text.lower() in ui_elements or any(ui in link_text.lower() for ui in ['return to', 'switch to', 'go to']):
                    continue
                
                # Skip navigation/settings links
                if any(skip in href.lower() for skip in ['_layouts', 'settings', 'sitecontents', 'appredirect', 'javascript:']):
                    continue
                
                # Make URL absolute
                if href.startswith('javascript:'):
                    continue
                elif href.startswith('/'):
                    full_url = urljoin(base_url, href)
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(current_url, href)
                
                url_normalized = full_url.split('?')[0].split('#')[0]
                
                # Check if it's a file (has file extension or common file patterns)
                is_file = any(ext in link_text.lower() or ext in url_normalized.lower() for ext in file_extensions)
                
                if is_file:
                    # This is a file - store for extraction
                    if (full_url, link_text, url_normalized) not in file_links:
                        file_links.append((full_url, link_text, url_normalized))
                        print(f"   [*] Found file: {link_text}")
                elif '/Forms/AllItems.aspx' in url_normalized or '/View.aspx' in url_normalized or '/Forms/' in url_normalized:
                    # This is a folder
                    if url_normalized.startswith('http') and url_normalized not in visited_urls:
                        if (url_normalized, link_text) not in folder_links:
                            folder_links.append((url_normalized, link_text))
                            print(f"   [*] Found subfolder: {link_text}")
            
            # Strategy 2: Use Selenium to find actual SharePoint list items (MOST RELIABLE)
            try:
                print(f"   [*] Searching for SharePoint items using Selenium selectors...")
                
                # Wait a bit for dynamic content to load
                time.sleep(2)
                
                # Multiple selectors for SharePoint modern UI items
                selectors = [
                    "[data-automation-id='FileRow']",  # File rows
                    "[data-automation-id='FolderRow']",  # Folder rows
                    ".od-ItemRow",  # OneDrive/SharePoint items
                    ".ms-DetailsRow",  # Details list rows
                    "[role='row']:not([role='columnheader'])",  # Data rows (not headers)
                    ".spListRow",  # SharePoint list rows
                ]
                
                all_rows = []
                for selector in selectors:
                    try:
                        rows = driver.find_elements(By.CSS_SELECTOR, selector)
                        if rows:
                            print(f"   [INFO] Found {len(rows)} items with selector: {selector}")
                            all_rows.extend(rows)
                    except:
                        continue
                
                # Remove duplicates based on element ID or position
                seen_elements = set()
                unique_rows = []
                for row in all_rows:
                    try:
                        element_id = row.get_attribute('id') or row.get_attribute('data-list-item-index') or str(row.location)
                        if element_id not in seen_elements:
                            seen_elements.add(element_id)
                            unique_rows.append(row)
                    except:
                        if row not in unique_rows:
                            unique_rows.append(row)
                
                print(f"   [INFO] Processing {len(unique_rows)} unique items...")
                
                for row in unique_rows[:100]:  # Limit to first 100 items
                    try:
                        # Try multiple methods to get the name/link
                        item_name = None
                        item_href = None
                        is_folder_item = False
                        
                        # Method 1: Find primary link in the row
                        try:
                            primary_link = row.find_element(By.CSS_SELECTOR, "a[href], [role='link']")
                            item_name = primary_link.text.strip()
                            item_href = primary_link.get_attribute('href')
                        except:
                            pass
                        
                        # Method 2: Get aria-label or title
                        if not item_name:
                            try:
                                item_name = row.get_attribute('aria-label') or row.get_attribute('title')
                            except:
                                pass
                        
                        # Method 3: Get text from the row
                        if not item_name:
                            try:
                                item_name = row.text.strip().split('\n')[0]  # First line
                            except:
                                pass
                        
                        # Check if it's a folder by looking for folder icons/indicators
                        try:
                            folder_indicators = row.find_elements(By.CSS_SELECTOR, 
                                "[class*='folder'], [class*='Folder'], [data-icon-name='FabricFolder'], [aria-label*='folder' i]")
                            is_folder_item = len(folder_indicators) > 0
                            
                            # Also check data-automation-id
                            automation_id = row.get_attribute('data-automation-id')
                            if automation_id and 'Folder' in automation_id:
                                is_folder_item = True
                        except:
                            pass
                        
                        # Check href pattern for folder
                        if item_href and ('/Forms/AllItems.aspx' in item_href or '/View.aspx' in item_href):
                            # But exclude if it's clearly a UI element
                            if 'return' in item_name.lower() or 'classic' in item_name.lower() or 'switch' in item_name.lower():
                                continue
                            is_folder_item = True
                        
                        if not item_name or len(item_name) < 1:
                            continue
                        
                        # Skip UI elements
                        item_lower = item_name.lower()
                        if any(skip in item_lower for skip in ['return to', 'classic sharepoint', 'switch', 'view all', 'refresh', 'new', 'upload', 'sync']):
                            continue
                        
                        # Skip if href is a UI link
                        if item_href and any(skip in item_href.lower() for skip in ['_layouts', 'settings', 'sitecontents', 'appredirect', 'javascript:']):
                            continue
                        
                        # Make URL absolute if needed
                        if item_href:
                            if item_href.startswith('javascript:'):
                                continue
                            elif item_href.startswith('/'):
                                full_url = urljoin(base_url, item_href)
                            elif item_href.startswith('http'):
                                full_url = item_href
                            else:
                                full_url = urljoin(current_url, item_href)
                            url_normalized = full_url.split('?')[0].split('#')[0]
                        else:
                            continue
                        
                        # Determine if it's a file or folder
                        has_file_ext = any(ext in item_name.lower() or (item_href and ext in url_normalized.lower()) for ext in file_extensions)
                        
                        if has_file_ext:
                            # It's a file
                            if (full_url, item_name, url_normalized) not in file_links:
                                file_links.append((full_url, item_name, url_normalized))
                                print(f"   [*] Found file (Selenium): {item_name}")
                        elif is_folder_item and url_normalized.startswith('http'):
                            # It's a folder (and not already visited)
                            if url_normalized not in visited_urls and (url_normalized, item_name) not in folder_links:
                                folder_links.append((url_normalized, item_name))
                                print(f"   [*] Found folder (Selenium): {item_name}")
                                
                    except Exception as e:
                        # Skip this row if there's an error
                        continue
                        
            except Exception as e:
                print(f"   [WARNING] Selenium element search failed: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"   [INFO] Total found: {len(file_links)} files, {len(folder_links)} folders")
            
            # If we found nothing, try waiting longer and scrolling more (SharePoint lazy loads)
            if len(file_links) == 0 and len(folder_links) == 0 and depth == 0:
                print(f"   [WARNING] No files or folders found at root - page may still be loading")
                print(f"   [INFO] Trying additional scrolls and waiting...")
                for _ in range(10):  # More scrolls for lazy-loaded content
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                time.sleep(5)  # Wait for lazy-loaded content
                
                # Re-parse page after scrolling
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Try finding links again
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True)
                    if not link_text or len(link_text) < 1:
                        continue
                    if link_text.lower() in ui_elements:
                        continue
                    if href.startswith('javascript:'):
                        continue
                    elif href.startswith('/'):
                        full_url = urljoin(base_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(current_url, href)
                    
                    url_normalized = full_url.split('?')[0].split('#')[0]
                    is_file = any(ext in link_text.lower() or ext in url_normalized.lower() for ext in file_extensions)
                    
                    if is_file:
                        if (full_url, link_text, url_normalized) not in file_links:
                            file_links.append((full_url, link_text, url_normalized))
                            print(f"   [*] Found file (after retry): {link_text}")
                    elif '/Forms/' in url_normalized or '/View.aspx' in url_normalized:
                        if url_normalized.startswith('http') and url_normalized not in visited_urls:
                            if (url_normalized, link_text) not in folder_links:
                                folder_links.append((url_normalized, link_text))
                                print(f"   [*] Found folder (after retry): {link_text}")
                
                print(f"   [INFO] After retry: {len(file_links)} files, {len(folder_links)} folders")
            
            # Extract content from each file
            for file_url, file_name, normalized_url in file_links:
                try:
                    print(f"   [*] Extracting content from: {file_name}")
                    
                    # Try to extract file content
                    file_content = self.extract_file_content(driver, file_url, file_name)
                    
                    # Build document content
                    doc_content_parts = [f"File: {file_name}"]
                    if folder_content_text:
                        doc_content_parts.append(f"Folder context: {folder_content_text[:500]}")
                    if file_content:
                        doc_content_parts.append(f"File content: {file_content[:10000]}")  # Limit content
                    else:
                        doc_content_parts.append(f"File location: {folder_name}")
                    
                    doc_content = "\n\n".join(doc_content_parts)
                    
                    # Check if it's a certificate:
                    # 1. Must be in a folder path containing "certificate" or "cert"
                    # 2. Must be in a "2025" year folder (latest certificates only)
                    folder_path_str = " > ".join(current_folder_path).lower()
                    is_certificate = (
                        ('certificate' in folder_path_str or 'cert' in folder_path_str) and
                        '2025' in folder_path_str
                    )
                    
                    # Check if it's a video (demo videos in Videos/Demos folder)
                    is_video = False
                    video_type = None
                    if any(ext in file_name.lower() for ext in ['.mp4', '.avi', '.mov', '.wmv', '.mkv']):
                        # Check if in Videos/Demos folder structure
                        if 'video' in folder_path_str and 'demo' in folder_path_str:
                            is_video = True
                            video_type = "demo_video"
                        elif 'video' in folder_path_str:
                            is_video = True
                            video_type = "video"
                    
                    if is_certificate:
                        print(f"   [INFO] Detected certificate (in 2025 folder): {file_name}")
                    if is_video:
                        print(f"   [INFO] Detected {video_type}: {file_name}")
                    
                    # Create document with download link in metadata
                    metadata = {
                        "source_type": "sharepoint",
                        "source": "cloudfuze_doc360",
                        "file_name": file_name,
                        "file_url": file_url,
                        "folder_path": " > ".join(current_folder_path),  # Human-readable path
                        "folder_tags": tag,  # Hierarchical tag for chatbot understanding
                        "tag": tag,  # Main tag field
                        "page_url": normalized_url,
                        "content_type": "sharepoint_video" if is_video else "sharepoint_file",
                        "is_certificate": is_certificate,
                        "depth": depth
                    }
                    
                    # Add download URL for certificates
                    if is_certificate:
                        metadata["download_url"] = file_url
                    
                    # Add video URL for videos
                    if is_video:
                        metadata["video_url"] = file_url
                        metadata["video_type"] = video_type
                        # For videos, store video filename for easier matching
                        metadata["video_name"] = file_name.rsplit('.', 1)[0]  # Name without extension
                    
                    doc = Document(
                        page_content=doc_content[:15000],
                        metadata=metadata
                    )
                    all_documents.append(doc)
                    print(f"   [OK] Extracted file: {file_name}")
                    
                except Exception as e:
                    print(f"   [ERROR] Error extracting file {file_name}: {e}")
                    # Still create a document with file name even if content extraction fails
                    # Check if it's a certificate (same logic as above)
                    folder_path_str_for_cert = " > ".join(current_folder_path).lower()
                    is_certificate_fallback = (
                        ('certificate' in folder_path_str_for_cert or 'cert' in folder_path_str_for_cert) and
                        '2025' in folder_path_str_for_cert
                    )
                    
                    # Check if it's a video
                    is_video_fallback = False
                    video_type_fallback = None
                    if any(ext in file_name.lower() for ext in ['.mp4', '.avi', '.mov', '.wmv', '.mkv']):
                        if 'video' in folder_path_str_for_cert and 'demo' in folder_path_str_for_cert:
                            is_video_fallback = True
                            video_type_fallback = "demo_video"
                        elif 'video' in folder_path_str_for_cert:
                            is_video_fallback = True
                            video_type_fallback = "video"
                    
                    metadata_fallback = {
                        "source_type": "sharepoint",
                        "source": "cloudfuze_doc360",
                        "file_name": file_name,
                        "file_url": file_url,
                        "folder_path": " > ".join(current_folder_path),
                        "folder_tags": tag,
                        "tag": tag,
                        "page_url": normalized_url,
                        "content_type": "sharepoint_video" if is_video_fallback else "sharepoint_file",
                        "is_certificate": is_certificate_fallback,
                        "depth": depth
                    }
                    
                    if is_certificate_fallback:
                        metadata_fallback["download_url"] = file_url
                    
                    if is_video_fallback:
                        metadata_fallback["video_url"] = file_url
                        metadata_fallback["video_type"] = video_type_fallback
                        metadata_fallback["video_name"] = file_name.rsplit('.', 1)[0]
                    
                    doc = Document(
                        page_content=f"File: {file_name}\nFolder: {folder_name}",
                        metadata=metadata_fallback
                    )
                    all_documents.append(doc)
            
            # Add folder structure document if there are items AND it contains useful content
            # Skip if it's mostly UI elements or very short
            if folder_content_text and len(folder_content_text.strip()) > 200:
                # Limit folder document size to avoid unnecessary large embeddings
                folder_doc = Document(
                    page_content=f"Folder: {folder_name}\n\n{folder_content_text[:5000]}",
                    metadata={
                        "source_type": "sharepoint",
                        "source": "cloudfuze_doc360",
                        "folder_name": folder_name,
                        "folder_path": " > ".join(current_folder_path),
                        "folder_tags": tag,
                        "tag": tag,
                        "page_url": current_url,
                        "content_type": "sharepoint_folder",
                        "depth": depth
                    }
                )
                all_documents.append(folder_doc)
            
            # Recursively explore subfolders (no depth limit) using DOUBLE-CLICK
            for folder_url, subfolder_name in folder_links:
                # Skip if already visited
                next_folder_path = current_folder_path.copy() + [subfolder_name]
                next_folder_key = " > ".join(next_folder_path)
                if next_folder_key in visited_urls:
                    print(f"   [SKIP] Already visited: {subfolder_name}")
                    continue
                
                try:
                    print(f"\n   [*] Opening subfolder via double-click: {subfolder_name}")
                    
                    # Find the folder element (need to find it on current page to double-click)
                    folder_element = None
                    
                    # Strategy 1: Find by link text
                    try:
                        folder_element = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, subfolder_name))
                        )
                    except:
                        pass
                    
                    # Strategy 2: Find by data attributes
                    if not folder_element:
                        try:
                            folder_element = driver.find_element(By.CSS_SELECTOR, f"[aria-label*='{subfolder_name}'], [title*='{subfolder_name}']")
                        except:
                            pass
                    
                    # Strategy 3: Find in table/list
                    if not folder_element:
                        try:
                            # Look for folder icon or folder row
                            all_links = driver.find_elements(By.TAG_NAME, "a")
                            for link in all_links:
                                if subfolder_name in link.text and ("/Forms/" in link.get_attribute('href') or "folder" in link.get_attribute('aria-label', '').lower()):
                                    folder_element = link
                                    break
                        except:
                            pass
                    
                    if folder_element:
                        # Scroll element into view
                        driver.execute_script("arguments[0].scrollIntoView(true);", folder_element)
                        time.sleep(1)
                        
                        # DOUBLE-CLICK the folder
                        ActionChains(driver).double_click(folder_element).perform()
                        print(f"   [OK] Double-clicked folder: {subfolder_name}")
                        
                        # Wait for folder to open
                        time.sleep(5)
                        
                        # Verify we're in the folder
                        new_url = driver.current_url
                        print(f"   [INFO] Now in folder (URL: {new_url})")
                        
                        # Extract from this subfolder
                        sub_docs = self.extract_from_documents_library(driver, new_url, visited_urls, depth + 1, next_folder_path)
                        all_documents.extend(sub_docs)
                        
                        # Navigate BACK using SharePoint breadcrumb (not browser back)
                        print(f"   [*] Navigating back from: {subfolder_name}")
                        self.navigate_back_in_sharepoint(driver)
                        time.sleep(3)  # Wait for navigation
                        
                    else:
                        print(f"   [ERROR] Could not find folder element to double-click: {subfolder_name}")
                        # Fallback: Try URL navigation (may not work but worth trying)
                        try:
                            driver.get(folder_url)
                            time.sleep(5)
                            sub_docs = self.extract_from_documents_library(driver, folder_url, visited_urls, depth + 1, next_folder_path)
                            all_documents.extend(sub_docs)
                        except Exception as e:
                            print(f"   [ERROR] Fallback navigation also failed: {e}")
                            
                except Exception as e:
                    print(f"   [ERROR] Error opening folder {subfolder_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
        except Exception as e:
            print(f"   [ERROR] Error extracting from {current_url}: {e}")
            import traceback
            traceback.print_exc()
        
        return all_documents


def extract_sharepoint_pages() -> List[Document]:
    """Main function for automated extraction."""
    extractor = SharePointSeleniumExtractor()
    return extractor.extract_all_pages()

if __name__ == "__main__":
    docs = extract_sharepoint_pages()
    print(f"\n📄 Total documents: {len(docs)}")
    
    for doc in docs:
        print(f"\n   - {doc.metadata.get('page_title')}: {len(doc.page_content)} chars")
