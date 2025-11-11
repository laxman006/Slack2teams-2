# -*- coding: utf-8 -*-
"""
SharePoint Content Diagnostic Tool

Check what SharePoint documents and paths are in the vectorstore.
"""

import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import CHROMA_DB_PATH
from collections import Counter, defaultdict

def check_sharepoint_content():
    """Check SharePoint documents in the vectorstore."""
    print("=" * 80)
    print("SHAREPOINT CONTENT DIAGNOSTIC")
    print("=" * 80)
    
    if not os.path.exists(CHROMA_DB_PATH):
        print("[!] No vectorstore found!")
        return
    
    try:
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings
        )
        
        total = vectorstore._collection.count()
        print(f"\n[*] Total documents in vectorstore: {total}")
        
        # Get all metadata
        print("[*] Scanning for SharePoint documents...")
        all_docs = vectorstore._collection.get(include=['metadatas'])
        
        # Collect SharePoint documents
        sharepoint_docs = []
        sharepoint_tags = Counter()
        sharepoint_paths = defaultdict(int)
        file_types = Counter()
        
        for idx, metadata in enumerate(all_docs['metadatas']):
            source_type = metadata.get('source_type', '')
            
            if source_type == 'sharepoint':
                sharepoint_docs.append(metadata)
                
                # Count tags
                tag = metadata.get('tag', 'unknown')
                sharepoint_tags[tag] += 1
                
                # Get file info
                file_name = metadata.get('file_name', 'unknown')
                folder_path = metadata.get('folder_path', 'unknown')
                file_extension = metadata.get('file_extension', 'unknown')
                
                # Count by folder path
                sharepoint_paths[folder_path] += 1
                
                # Count by file type
                if file_extension:
                    file_types[file_extension] += 1
        
        print(f"\n[*] Found {len(sharepoint_docs)} SharePoint documents")
        
        if not sharepoint_docs:
            print("\n[!] No SharePoint documents found in vectorstore")
            print("    Set ENABLE_SHAREPOINT_SOURCE=true and INITIALIZE_VECTORSTORE=true to load")
            return
        
        # Display by hierarchical tags
        print("\n" + "=" * 80)
        print("SHAREPOINT DOCUMENTS BY TAG (Hierarchical Paths)")
        print("=" * 80)
        
        for tag, count in sorted(sharepoint_tags.items()):
            print(f"  {tag}: {count} chunks")
        
        # Display by folder paths
        print("\n" + "=" * 80)
        print("SHAREPOINT DOCUMENTS BY FOLDER PATH")
        print("=" * 80)
        
        for path, count in sorted(sharepoint_paths.items()):
            print(f"  {path}: {count} chunks")
        
        # Display by file type
        print("\n" + "=" * 80)
        print("SHAREPOINT DOCUMENTS BY FILE TYPE")
        print("=" * 80)
        
        for ext, count in sorted(file_types.items(), key=lambda x: -x[1]):
            print(f"  {ext}: {count} chunks")
        
        # Show unique files
        print("\n" + "=" * 80)
        print("UNIQUE FILES IN SHAREPOINT")
        print("=" * 80)
        
        unique_files = {}
        for metadata in sharepoint_docs:
            file_name = metadata.get('file_name', 'unknown')
            folder_path = metadata.get('folder_path', 'unknown')
            file_key = f"{folder_path}/{file_name}"
            
            if file_key not in unique_files:
                unique_files[file_key] = {
                    'name': file_name,
                    'path': folder_path,
                    'extension': metadata.get('file_extension', ''),
                    'is_downloadable': metadata.get('is_downloadable', False),
                    'download_url': metadata.get('download_url', ''),
                    'chunks': 1
                }
            else:
                unique_files[file_key]['chunks'] += 1
        
        print(f"\n[*] Total unique files: {len(unique_files)}")
        print()
        
        # Sort by folder path
        for file_key in sorted(unique_files.keys()):
            file_info = unique_files[file_key]
            downloadable = "✓ Downloadable" if file_info['is_downloadable'] else ""
            
            print(f"📄 {file_info['name']}")
            print(f"   Path: {file_info['path']}")
            print(f"   Type: {file_info['extension']}")
            print(f"   Chunks: {file_info['chunks']}")
            if downloadable:
                print(f"   {downloadable}")
            print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total SharePoint chunks: {len(sharepoint_docs)}")
        print(f"Unique files: {len(unique_files)}")
        print(f"Unique folders: {len(sharepoint_paths)}")
        print(f"File types: {len(file_types)}")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_sharepoint_content()

