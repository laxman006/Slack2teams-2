#!/usr/bin/env python3
"""
Compare SharePoint Content Titles
Extracts titles from parent site and child page, finds what's missing in parent
"""

import os
import time
from typing import List, Set, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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
    print("ERROR: Selenium not installed. Run: pip install selenium webdriver-manager")

def setup_driver():
    """Setup Chrome WebDriver."""
    if not SELENIUM_AVAILABLE:
        raise ImportError("Selenium not available")
    
    chrome_options = Options()
    # Keep browser visible for manual login
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    
    return driver

def extract_titles(driver, url: str) -> Set[str]:
    """Extract all titles/headings from a SharePoint page."""
    print(f"\n[*] Extracting titles from: {url}")
    driver.get(url)
    time.sleep(3)
    
    # Wait for authentication if needed
    if "login.microsoftonline.com" in driver.current_url or "signin" in driver.current_url:
        print("[WARNING] Authentication required!")
        print("[INFO] Please sign in to SharePoint in the browser window")
        print("[INFO] Waiting for authentication (max 2 minutes)...")
        
        wait_time = 0
        while ("login" in driver.current_url.lower() or "signin" in driver.current_url.lower()) and wait_time < 120:
            time.sleep(2)
            wait_time += 2
        
        if "login" in driver.current_url.lower() or "signin" in driver.current_url.lower():
            print("[ERROR] Authentication timeout")
            return set()
    
    # Wait for page to fully load
    time.sleep(5)
    
    # Scroll to load all content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    titles = set()
    
    # Extract heading tags (h1-h6)
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = heading.get_text(strip=True)
        if text and len(text) > 3:  # Filter out very short text
            titles.add(text.lower())
    
    # Extract title attributes and aria-labels
    for elem in soup.find_all(attrs={'title': True}):
        title_text = elem.get('title', '').strip()
        if title_text and len(title_text) > 3:
            titles.add(title_text.lower())
    
    # Extract link texts (often titles in SharePoint)
    for link in soup.find_all('a', href=True):
        link_text = link.get_text(strip=True)
        if link_text and len(link_text) > 3:
            titles.add(link_text.lower())
    
    # Extract SharePoint document titles
    for elem in soup.find_all(class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower())):
        text = elem.get_text(strip=True)
        if text and len(text) > 3:
            titles.add(text.lower())
    
    # Extract from data attributes
    for elem in soup.find_all(attrs={'data-title': True}):
        text = elem.get('data-title', '').strip()
        if text and len(text) > 3:
            titles.add(text.lower())
    
    print(f"[OK] Extracted {len(titles)} unique titles")
    return titles

def extract_from_current_folder(driver, current_url: str, visited_urls: Set[str], max_depth: int = 5, current_depth: int = 0) -> Set[str]:
    """Recursively extract document/folder titles from current folder and subfolders."""
    if current_depth > max_depth or current_url in visited_urls:
        return set()
    
    visited_urls.add(current_url)
    all_titles = set()
    
    try:
        print(f"[*] Depth {current_depth}: Exploring {current_url}")
        driver.get(current_url)
        time.sleep(4)
        
        # Scroll multiple times to load all items
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract document/file names - multiple methods for SharePoint modern UI
        # Method 1: data-automation-id attribute
        for elem in soup.find_all(['a', 'div', 'span'], attrs={'data-automation-id': True}):
            text = elem.get_text(strip=True)
            if text and len(text) > 2:
                all_titles.add(text.lower())
        
        # Method 2: aria-label attribute (often contains file/folder names)
        for elem in soup.find_all(['a', 'button', 'div'], attrs={'aria-label': True}):
            aria_label = elem.get('aria-label', '').strip()
            if aria_label and len(aria_label) > 2 and 'folder' not in aria_label.lower():
                all_titles.add(aria_label.lower())
        
        # Method 3: SharePoint list view cells
        for item in soup.find_all(['div', 'span', 'td'], class_=lambda x: x and (
            'ms-DetailsRow-cell' in x or 
            'ms-List-cell' in x or 
            'FileTypeIcon' in x or
            'file-name' in x.lower() or
            'name-cell' in x.lower() or
            'ms-DetailsList-cell' in x
        )):
            text = item.get_text(strip=True)
            if text and len(text) > 2:
                # Skip common UI elements and column headers
                ui_words = ['name', 'modified', 'modified by', 'type', 'size', 'title', 'created', 'author', 'select']
                if not any(word in text.lower() for word in ui_words):
                    all_titles.add(text.lower())
        
        # Method 4: Modern SharePoint file picker and grid views
        for elem in soup.find_all(['div', 'span'], attrs={'role': lambda x: x in ['button', 'link', 'gridcell']}):
            text = elem.get_text(strip=True)
            if text and len(text) > 2:
                # Skip common UI
                if text.lower() not in ['view', 'edit', 'share', 'more', 'open', 'download']:
                    all_titles.add(text.lower())
        
        # Extract all links that might be files/folders
        base_url = current_url.rsplit('/', 1)[0] if '/' in current_url else current_url
        
        # Find folder icons/indicators first
        folder_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            link_text = link.get_text(strip=True)
            
            if not link_text or len(link_text) < 2:
                continue
            
            # Check if parent element has folder indicators
            parent = link.parent if link.parent else None
            folder_indicator = False
            
            # Check for folder icon class or data attributes
            if parent:
                parent_classes = ' '.join(parent.get('class', []))
                if 'folder' in parent_classes.lower() or 'ms-FolderLink' in parent_classes:
                    folder_indicator = True
            
            # Check href patterns for folders
            if '/Forms/AllItems.aspx' in href or '/View.aspx' in href or '/Forms/' in href:
                folder_indicator = True
            
            # Check for folder icon in nearby elements
            if parent:
                # Look for folder icon classes
                folder_icons = parent.find_all(['i', 'svg', 'img'], class_=lambda x: x and ('folder' in x.lower() or 'ms-Folder' in x))
                if folder_icons:
                    folder_indicator = True
            
            # Also check if link text suggests it's a folder (but not a file extension)
            file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.jpg', '.png']
            if not any(ext in link_text.lower() for ext in file_extensions) and len(link_text) > 2:
                # Might be a folder if it doesn't have a file extension
                if '/Shared Documents/' in href or '/Documents/' in href:
                    folder_indicator = True
            
            # Check aria-label for folder
            aria_label = link.get('aria-label', '')
            if 'folder' in aria_label.lower():
                folder_indicator = True
            
            # Make URL absolute
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(current_url, href)
            
            # Normalize URL (remove fragments, query params for comparison)
            url_normalized = full_url.split('?')[0].split('#')[0]
            
            # Skip JavaScript links and non-HTTP URLs
            if url_normalized.startswith('javascript:') or not url_normalized.startswith('http'):
                folder_indicator = False
            
            # If it's a folder, explore it recursively
            if folder_indicator and url_normalized not in visited_urls and current_depth < max_depth and url_normalized.startswith('http'):
                print(f"  [*] Found folder: {link_text} -> {url_normalized}")
                folder_links.append((url_normalized, link_text))
            
            # Always add the link text as a title (for files)
            if link_text.lower() not in ['view', 'edit', 'share', 'download', 'more', 'open', 'name', 'modified']:
                all_titles.add(link_text.lower())
        
        # Now recursively explore each found folder
        for folder_url, folder_name in folder_links:
            print(f"  [*] Exploring subfolder: {folder_name}")
            folder_titles = extract_from_current_folder(driver, folder_url, visited_urls, max_depth, current_depth + 1)
            all_titles.update(folder_titles)
        
        # Extract from table cells (SharePoint list views)
        for cell in soup.find_all(['td', 'th']):
            text = cell.get_text(strip=True)
            if text and len(text) > 2:
                # Skip column headers
                if text.lower() not in ['name', 'modified', 'modified by', 'type', 'size', 'title', 'created', 'author']:
                    all_titles.add(text.lower())
        
    except Exception as e:
        print(f"[WARNING] Error extracting from {current_url}: {e}")
    
    return all_titles

def extract_parent_document_titles(driver, parent_url: str) -> Set[str]:
    """Extract titles from all documents/folders in parent site recursively."""
    print(f"\n[*] Extracting titles from parent site: {parent_url}")
    driver.get(parent_url)
    time.sleep(3)
    
    # Wait for authentication if needed
    if "login.microsoftonline.com" in driver.current_url or "signin" in driver.current_url:
        print("[WARNING] Authentication required!")
        print("[INFO] Please sign in to SharePoint in the browser window")
        print("[INFO] Waiting for authentication (max 2 minutes)...")
        
        wait_time = 0
        while ("login" in driver.current_url.lower() or "signin" in driver.current_url.lower()) and wait_time < 120:
            time.sleep(2)
            wait_time += 2
        
        if "login" in driver.current_url.lower() or "signin" in driver.current_url.lower():
            print("[ERROR] Authentication timeout")
            return set()
    
    # Wait for page to fully load
    time.sleep(5)
    
    visited_urls = set()
    all_titles = set()
    
    # Try to navigate to Documents library
    try:
        print("[*] Looking for Documents library...")
        
        # Try clicking on Documents link
        doc_selectors = [
            (By.PARTIAL_LINK_TEXT, "Document"),
            (By.PARTIAL_LINK_TEXT, "Shared Documents"),
            (By.XPATH, "//a[contains(text(), 'Document')]"),
            (By.XPATH, "//a[contains(@href, '/Shared Documents')]"),
            (By.XPATH, "//a[contains(@href, '/Documents')]")
        ]
        
        documents_url = None
        for selector_type, selector_value in doc_selectors:
            try:
                elements = driver.find_elements(selector_type, selector_value)
                for elem in elements:
                    href = elem.get_attribute('href')
                    if href and ('Document' in href or '/Shared' in href):
                        documents_url = href
                        print(f"[*] Found Documents library: {documents_url}")
                        break
                if documents_url:
                    break
            except:
                continue
        
        if not documents_url:
            # Try to construct the URL directly
            if parent_url.endswith('/'):
                documents_url = parent_url + "Shared Documents/Forms/AllItems.aspx"
            else:
                documents_url = parent_url + "/Shared Documents/Forms/AllItems.aspx"
            print(f"[*] Using default Documents URL: {documents_url}")
        
        # Start recursive extraction from Documents library
        if documents_url:
            all_titles.update(extract_from_current_folder(driver, documents_url, visited_urls, max_depth=5, current_depth=0))
        
    except Exception as e:
        print(f"[WARNING] Error accessing Documents library: {e}")
    
    # Also extract from the main page itself
    try:
        print("[*] Extracting from main page...")
        driver.get(parent_url)
        time.sleep(3)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text(strip=True)
            if text and len(text) > 3:
                all_titles.add(text.lower())
        
        # Extract link texts (skip UI elements)
        ui_keywords = ['browse', 'edit', 'settings', 'help', 'search', 'skip', 'site', 'page', 'publish']
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            if link_text and len(link_text) > 3:
                if not any(keyword in link_text.lower() for keyword in ui_keywords):
                    all_titles.add(link_text.lower())
    except Exception as e:
        print(f"[WARNING] Error extracting from main page: {e}")
    
    print(f"[OK] Extracted {len(all_titles)} unique titles from parent (explored {len(visited_urls)} folders)")
    return all_titles

def main():
    """Main comparison function."""
    if not SELENIUM_AVAILABLE:
        print("ERROR: Selenium not installed")
        print("Run: pip install selenium webdriver-manager")
        return
    
    parent_url = "https://cloudfuzecom.sharepoint.com/sites/DOC360"
    child_url = "https://cloudfuzecom.sharepoint.com/sites/DOC360/SitePages/Multi%20User%20Golden%20Image%20Combinations.aspx"
    
    print("=" * 80)
    print("SHAREPOINT TITLE COMPARISON")
    print("=" * 80)
    print(f"Parent URL: {parent_url}")
    print(f"Child URL: {child_url}")
    print("=" * 80)
    
    driver = None
    
    try:
        driver = setup_driver()
        print("[OK] Chrome browser opened")
        
        # Extract titles from child page
        child_titles = extract_titles(driver, child_url)
        
        # Extract titles from parent site
        parent_titles = extract_parent_document_titles(driver, parent_url)
        
        # Find missing titles (in child but not in parent)
        missing_titles = child_titles - parent_titles
        
        # Results
        print("\n" + "=" * 80)
        print("COMPARISON RESULTS")
        print("=" * 80)
        print(f"Total titles in child page: {len(child_titles)}")
        print(f"Total titles in parent site: {len(parent_titles)}")
        print(f"Titles in child but MISSING in parent: {len(missing_titles)}")
        print("=" * 80)
        
        if missing_titles:
            # Filter out common UI elements
            ui_keywords = [
                'browse', 'edit', 'settings', 'help', 'search', 'skip', 'site', 'page', 'publish',
                'change properties', 'close this web part', 'collapse', 'expand', 'delete this web part',
                'export this web part', 'show connections', 'pick where', 'focus on', 'turn off',
                'turn on', 'this animation', 'more accessible mode', 'ribbon commands', 'tab'
            ]
            
            # Actual content titles (filtered)
            actual_missing = []
            ui_missing = []
            
            for title in sorted(missing_titles):
                if any(keyword in title for keyword in ui_keywords):
                    ui_missing.append(title)
                else:
                    actual_missing.append(title)
            
            print("\n[MISSING] Actual Content Titles (not UI elements) missing in parent:")
            print("-" * 80)
            if actual_missing:
                for i, title in enumerate(actual_missing, 1):
                    print(f"{i}. {title}")
            else:
                print("  (All missing titles are UI elements)")
            
            if ui_missing:
                print(f"\n[INFO] Also found {len(ui_missing)} UI-related titles (excluded from main list)")
        else:
            print("\n[OK] All child page titles are present in parent site!")
        
        # Also show common titles for reference
        common_titles = child_titles & parent_titles
        if common_titles:
            print(f"\n[COMMON] Common titles ({len(common_titles)}): {list(sorted(common_titles))[:10]}...")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            print("\n[*] Keeping browser open for 10 seconds...")
            time.sleep(10)
            driver.quit()
            print("[OK] Browser closed")

if __name__ == "__main__":
    main()

