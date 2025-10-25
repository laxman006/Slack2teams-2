#!/usr/bin/env python3
"""
Test script for individual source control system
"""

import os
import sys

def test_source_control():
    """Test the individual source control system."""
    print("=" * 60)
    print("TESTING INDIVIDUAL SOURCE CONTROL SYSTEM")
    print("=" * 60)
    
    # Test current configuration
    from config import (
        ENABLE_WEB_SOURCE, ENABLE_PDF_SOURCE, 
        ENABLE_EXCEL_SOURCE, ENABLE_DOC_SOURCE,
        WEB_SOURCE_URL, PDF_SOURCE_DIR, 
        EXCEL_SOURCE_DIR, DOC_SOURCE_DIR
    )
    
    print("Current Configuration:")
    print(f"  Web Source: {ENABLE_WEB_SOURCE} (URL: {WEB_SOURCE_URL})")
    print(f"  PDF Source: {ENABLE_PDF_SOURCE} (Dir: {PDF_SOURCE_DIR})")
    print(f"  Excel Source: {ENABLE_EXCEL_SOURCE} (Dir: {EXCEL_SOURCE_DIR})")
    print(f"  Doc Source: {ENABLE_DOC_SOURCE} (Dir: {DOC_SOURCE_DIR})")
    
    # Check which sources would be processed
    enabled_sources = []
    if ENABLE_WEB_SOURCE:
        enabled_sources.append("Web content")
    
    if ENABLE_PDF_SOURCE and os.path.exists(PDF_SOURCE_DIR):
        pdf_files = [f for f in os.listdir(PDF_SOURCE_DIR) if f.lower().endswith('.pdf')]
        if pdf_files:
            enabled_sources.append(f"PDFs ({len(pdf_files)} files)")
        else:
            enabled_sources.append("PDFs (no files found)")
    elif ENABLE_PDF_SOURCE:
        enabled_sources.append("PDFs (directory not found)")
    
    if ENABLE_EXCEL_SOURCE and os.path.exists(EXCEL_SOURCE_DIR):
        excel_files = [f for f in os.listdir(EXCEL_SOURCE_DIR) if f.lower().endswith(('.xlsx', '.xls'))]
        if excel_files:
            enabled_sources.append(f"Excel files ({len(excel_files)} files)")
        else:
            enabled_sources.append("Excel files (no files found)")
    elif ENABLE_EXCEL_SOURCE:
        enabled_sources.append("Excel files (directory not found)")
    
    if ENABLE_DOC_SOURCE and os.path.exists(DOC_SOURCE_DIR):
        doc_files = [f for f in os.listdir(DOC_SOURCE_DIR) if f.lower().endswith(('.docx', '.doc'))]
        if doc_files:
            enabled_sources.append(f"Word documents ({len(doc_files)} files)")
        else:
            enabled_sources.append("Word documents (no files found)")
    elif ENABLE_DOC_SOURCE:
        enabled_sources.append("Word documents (directory not found)")
    
    print(f"\nSources that would be processed:")
    for source in enabled_sources:
        print(f"  [OK] {source}")
    
    if not enabled_sources:
        print("  [WARNING] No sources enabled!")
    
    print("\n" + "=" * 60)

def test_metadata():
    """Test metadata generation for enabled sources."""
    try:
        from app.vectorstore import get_current_metadata
        metadata = get_current_metadata()
        
        print("Generated Metadata:")
        print(f"  Timestamp: {metadata.get('timestamp')}")
        print(f"  Enabled sources: {metadata.get('enabled_sources', [])}")
        
        if 'url' in metadata:
            print(f"  Web URL: {metadata.get('url')}")
        if 'pdfs' in metadata:
            print(f"  PDFs hash: {metadata.get('pdfs')[:16]}...")
        if 'excel' in metadata:
            print(f"  Excel hash: {metadata.get('excel')[:16]}...")
        if 'docs' in metadata:
            print(f"  Docs hash: {metadata.get('docs')[:16]}...")
            
    except Exception as e:
        print(f"Error testing metadata: {e}")

if __name__ == "__main__":
    test_source_control()
    test_metadata()
