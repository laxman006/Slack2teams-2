#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check SharePoint Coverage - Compare vectorstore content vs available SharePoint files
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.vectorstore import vectorstore
    from app.sharepoint_graph_extractor import extract_sharepoint_files_graph
    from app.sharepoint_auth import get_sharepoint_access_token, SHAREPOINT_SITE_ID
    from config import SHAREPOINT_SITE_URL, SHAREPOINT_EXCLUDE_FOLDERS
    from collections import Counter
    
    print("=" * 80)
    print("  SHAREPOINT COVERAGE ANALYSIS")
    print("=" * 80)
    
    # Get vectorstore content
    print("\n[1] Analyzing Vectorstore Content...")
    collection = vectorstore._collection
    results = collection.get(limit=10000, include=['metadatas'])
    
    vectorstore_files = set()
    vectorstore_tags = []
    
    for metadata in results['metadatas']:
        if metadata.get('source_type') == 'sharepoint':
            tag = metadata.get('tag', '')
            vectorstore_tags.append(tag)
            # Extract file path from tag (format: sharepoint/path/to/file.ext)
            if tag.startswith('sharepoint/'):
                file_path = tag.replace('sharepoint/', '')
                vectorstore_files.add(file_path)
    
    print(f"   ✓ Vectorstore has {len(vectorstore_files)} unique SharePoint files")
    print(f"   ✓ Total SharePoint chunks: {len(vectorstore_tags)}")
    
    # Get SharePoint content
    print("\n[2] Fetching Available SharePoint Files...")
    print(f"   Site: {SHAREPOINT_SITE_URL}")
    
    try:
        access_token = get_sharepoint_access_token()
        sharepoint_docs = extract_sharepoint_files_graph(
            access_token=access_token,
            site_id=SHAREPOINT_SITE_ID
        )
        
        sharepoint_files = set()
        sharepoint_by_type = Counter()
        
        for doc in sharepoint_docs:
            file_path = doc.metadata.get('file_path', '')
            filetype = doc.metadata.get('filetype', 'unknown')
            sharepoint_files.add(file_path)
            sharepoint_by_type[filetype] += 1
        
        print(f"   ✓ SharePoint has {len(sharepoint_files)} total files")
        
        print("\n   File types in SharePoint:")
        for filetype, count in sharepoint_by_type.most_common():
            print(f"      {filetype.upper():10s}: {count}")
        
    except Exception as e:
        print(f"   ⚠ Could not fetch SharePoint content: {e}")
        print("   ⚠ Skipping comparison (will only show vectorstore content)")
        sharepoint_files = set()
    
    # Compare
    print("\n" + "=" * 80)
    print("  COMPARISON RESULTS")
    print("=" * 80)
    
    if sharepoint_files:
        missing_files = sharepoint_files - vectorstore_files
        extra_files = vectorstore_files - sharepoint_files
        
        print(f"\n✓ Files in Vectorstore: {len(vectorstore_files)}")
        print(f"✓ Files in SharePoint: {len(sharepoint_files)}")
        print(f"✓ Coverage: {len(vectorstore_files)/max(len(sharepoint_files), 1)*100:.1f}%")
        
        if missing_files:
            print(f"\n⚠ Missing from Vectorstore: {len(missing_files)} files")
            if len(missing_files) <= 20:
                print("\n   Missing files:")
                for f in sorted(missing_files)[:20]:
                    print(f"   - {f}")
            else:
                print("\n   Sample missing files:")
                for f in sorted(missing_files)[:20]:
                    print(f"   - {f}")
                print(f"   ... and {len(missing_files) - 20} more")
        else:
            print("\n✅ ALL SharePoint files are in vectorstore!")
        
        if extra_files:
            print(f"\n⚠ Extra in Vectorstore (not in SharePoint): {len(extra_files)} files")
    else:
        print(f"\n✓ Vectorstore contains: {len(vectorstore_files)} unique SharePoint files")
        print(f"✓ Total chunks: {len(vectorstore_tags)}")
        print("\n   (Could not fetch SharePoint content for comparison)")
    
    # Show excluded folders
    print("\n" + "=" * 80)
    print("  EXCLUDED FOLDERS (Not Ingested)")
    print("=" * 80)
    if SHAREPOINT_EXCLUDE_FOLDERS:
        for folder in SHAREPOINT_EXCLUDE_FOLDERS:
            print(f"   ✗ {folder}")
    else:
        print("   (No folders excluded)")
    
    # Summary
    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    
    # Count folders represented
    folder_counts = Counter()
    for tag in vectorstore_tags:
        if tag.startswith('sharepoint/'):
            parts = tag.replace('sharepoint/', '').split('/')
            if len(parts) > 0:
                folder_counts[parts[0]] += 1
    
    print(f"\n📁 Top Folders in Vectorstore:")
    for folder, count in folder_counts.most_common(10):
        print(f"   {folder:40s}: {count:4d} chunks")
    
    print("\n" + "=" * 80)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

