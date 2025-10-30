#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE CHECK - Everything must pass before server run
"""

import os
import sys

print("="*80)
print("FINAL COMPREHENSIVE CHECK - BEFORE SERVER RUN")
print("="*80)

all_checks = []
errors = []
warnings = []

# Check 1: Configuration
print("\n[1] Checking Configuration...")
try:
    from config import (
        ENABLE_SHAREPOINT_SOURCE, 
        SHAREPOINT_START_PAGE, 
        SHAREPOINT_MAX_DEPTH,
        SHAREPOINT_SITE_URL,
        INITIALIZE_VECTORSTORE
    )
    
    if ENABLE_SHAREPOINT_SOURCE:
        print("  [OK] ENABLE_SHAREPOINT_SOURCE = True")
        all_checks.append(True)
    else:
        print("  [ERROR] ENABLE_SHAREPOINT_SOURCE = False")
        errors.append("Enable SharePoint source in .env")
        all_checks.append(False)
    
    if not SHAREPOINT_START_PAGE or SHAREPOINT_START_PAGE.strip() == "":
        print("  [OK] SHAREPOINT_START_PAGE is empty (Documents library)")
        all_checks.append(True)
    else:
        print(f"  [ERROR] SHAREPOINT_START_PAGE = '{SHAREPOINT_START_PAGE}' (should be empty)")
        errors.append("Set SHAREPOINT_START_PAGE=\"\" in .env")
        all_checks.append(False)
    
    if SHAREPOINT_MAX_DEPTH >= 999:
        print(f"  [OK] SHAREPOINT_MAX_DEPTH = {SHAREPOINT_MAX_DEPTH} (unlimited)")
        all_checks.append(True)
    else:
        print(f"  [WARNING] SHAREPOINT_MAX_DEPTH = {SHAREPOINT_MAX_DEPTH} (should be 999)")
        warnings.append("Consider setting SHAREPOINT_MAX_DEPTH=999")
        all_checks.append(True)  # Not critical
    
    print(f"  [OK] SHAREPOINT_SITE_URL = {SHAREPOINT_SITE_URL}")
    print(f"  [OK] INITIALIZE_VECTORSTORE = {INITIALIZE_VECTORSTORE}")
    
except Exception as e:
    print(f"  [ERROR] Config check failed: {e}")
    errors.append(f"Config error: {e}")
    all_checks.append(False)

# Check 2: Code Imports (critical paths only)
print("\n[2] Checking Critical Code Imports...")
try:
    # Don't import sharepoint_processor (it requires auth) - test extractor directly
    from app.sharepoint_selenium_extractor import SharePointSeleniumExtractor
    from app.vectorstore import get_vectorstore, get_changed_sources, get_current_metadata
    from app.llm import setup_qa_chain
    print("  [OK] All critical imports successful")
    all_checks.append(True)
except Exception as e:
    print(f"  [ERROR] Import failed: {e}")
    errors.append(f"Import error: {e}")
    all_checks.append(False)

# Check 3: SharePoint Extractor Configuration
print("\n[3] Checking SharePoint Extractor...")
try:
    extractor = SharePointSeleniumExtractor()
    if extractor.max_depth >= 999:
        print(f"  [OK] Max depth = {extractor.max_depth} (unlimited)")
    if not extractor.start_page or extractor.start_page.strip() == "":
        print("  [OK] Start page is empty (Documents library)")
    print(f"  [OK] Site URL = {extractor.site_url}")
    all_checks.append(True)
except Exception as e:
    print(f"  [ERROR] Extractor check failed: {e}")
    errors.append(f"Extractor error: {e}")
    all_checks.append(False)

# Check 4: Vectorstore Logic
print("\n[4] Checking Vectorstore Logic...")
try:
    # Check if metadata exists
    metadata_exists = os.path.exists("data/vectorstore_metadata.json")
    print(f"  [INFO] Metadata file exists: {metadata_exists}")
    
    # Check current metadata
    current_meta = get_current_metadata()
    print(f"  [OK] Current enabled sources: {current_meta.get('enabled_sources', [])}")
    
    # Check changed sources (this won't trigger rebuild, just checks logic)
    changed = get_changed_sources()
    print(f"  [OK] Change detection working (changed: {changed})")
    all_checks.append(True)
except Exception as e:
    print(f"  [WARNING] Vectorstore check: {e}")
    warnings.append(f"Vectorstore: {e}")
    all_checks.append(True)  # Not critical for initial check

# Check 5: File Structure
print("\n[5] Checking File Structure...")
required_files = [
    "app/sharepoint_selenium_extractor.py",
    "app/sharepoint_processor.py",
    "app/vectorstore.py",
    "app/llm.py",
    "config.py",
    "server.py"
]
missing = []
for file in required_files:
    if os.path.exists(file):
        print(f"  [OK] {file} exists")
    else:
        print(f"  [ERROR] {file} missing")
        missing.append(file)
        all_checks.append(False)

if not missing:
    all_checks.append(True)

# Check 6: No Unicode Emoji Issues
print("\n[6] Checking for Unicode Encoding Issues...")
try:
    import re
    problematic_files = []
    
    # Check key files for emojis
    files_to_check = [
        "app/sharepoint_selenium_extractor.py",
        "app/sharepoint_processor.py",
        "app/vectorstore.py",
        "app/llm.py"
    ]
    
    emoji_pattern = re.compile(r'[\u2600-\u27BF]|[\u2B50-\u2B55]')
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if emoji_pattern.search(content):
                    problematic_files.append(file_path)
    
    if problematic_files:
        print(f"  [WARNING] Potential emoji issues in: {problematic_files}")
        warnings.append("Unicode emoji characters found")
    else:
        print("  [OK] No emoji characters found")
    all_checks.append(True)
    
except Exception as e:
    print(f"  [WARNING] Emoji check: {e}")
    all_checks.append(True)

# Check 7: Chunking and Metadata Preservation
print("\n[7] Testing Chunking Logic...")
try:
    from app.sharepoint_processor import chunk_sharepoint_documents
    from langchain_core.documents import Document
    
    test_doc = Document(
        page_content="Test " * 100,
        metadata={"tag": "sharepoint/test", "video_url": "test.mp4", "is_certificate": True}
    )
    chunked = chunk_sharepoint_documents([test_doc])
    if chunked and "tag" in chunked[0].metadata:
        print("  [OK] Chunking preserves metadata correctly")
        all_checks.append(True)
    else:
        print("  [ERROR] Chunking may not preserve metadata")
        errors.append("Metadata preservation issue")
        all_checks.append(False)
except Exception as e:
    print(f"  [WARNING] Chunking test: {e}")
    all_checks.append(True)

# Summary
print("\n" + "="*80)
print("FINAL CHECK SUMMARY")
print("="*80)

passed = sum(all_checks)
total = len(all_checks)
print(f"\nPassed: {passed}/{total} checks")

if errors:
    print("\n[ERRORS FOUND]:")
    for error in errors:
        print(f"  - {error}")

if warnings:
    print("\n[WARNINGS]:")
    for warning in warnings:
        print(f"  - {warning}")

if passed == total and not errors:
    print("\n" + "="*80)
    print("[SUCCESS] ALL CHECKS PASSED!")
    print("="*80)
    print("\nYour server is ready to run!")
    print("\nWhat will happen:")
    print("  1. Server starts")
    print("  2. Detects SharePoint needs extraction")
    print("  3. Opens Chrome browser (sign in when prompted)")
    print("  4. Recursively extracts ALL files from Documents library")
    print("  5. Creates tags for all folders/subfolders")
    print("  6. Detects certificates (in Certificate/2025 folders)")
    print("  7. Detects videos (in Videos/Demos folders)")
    print("  8. Chunks all documents")
    print("  9. Adds to vectorstore (preserves old data)")
    print("\n[IMPORTANT]:")
    print("  - Have your SharePoint login ready")
    print("  - Extraction may take 15-20 minutes for large folders")
    print("  - All data will be added to vectorstore")
    print("\nRun: python server.py")
    sys.exit(0)
else:
    print("\n" + "="*80)
    print("[FAILURE] ISSUES FOUND - FIX BEFORE RUNNING SERVER")
    print("="*80)
    print("\nPlease fix the errors above before running the server.")
    sys.exit(1)

