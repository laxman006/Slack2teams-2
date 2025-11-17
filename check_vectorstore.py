#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check Vectorstore Contents - Verify what data is actually stored
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.vectorstore import vectorstore
    import chromadb
    from collections import Counter
    
    print("=" * 80)
    print("  VECTORSTORE CONTENT ANALYSIS")
    print("=" * 80)
    
    if vectorstore is None:
        print("\n❌ ERROR: Vectorstore is not initialized!")
        print("   Please run: python server.py or rebuild the vectorstore")
        sys.exit(1)
    
    # Get the collection
    collection = vectorstore._collection
    
    # Get total count
    total_count = collection.count()
    print(f"\n📊 Total Documents: {total_count}")
    
    if total_count == 0:
        print("\n❌ WARNING: Vectorstore is EMPTY!")
        print("   You need to run the ingestion process to add documents.")
        sys.exit(0)
    
    # Get all documents (limit to reasonable number for analysis)
    sample_size = min(total_count, 1000)
    results = collection.get(
        limit=sample_size,
        include=['metadatas', 'documents']
    )
    
    print(f"\n📝 Analyzing {len(results['ids'])} documents...\n")
    
    # Analyze metadata
    source_types = Counter()
    tags = Counter()
    file_types = Counter()
    sources = Counter()
    
    for metadata in results['metadatas']:
        source_type = metadata.get('source_type', 'unknown')
        tag = metadata.get('tag', 'unknown')
        filetype = metadata.get('filetype', 'unknown')
        source = metadata.get('source', 'unknown')
        
        source_types[source_type] += 1
        tags[tag] += 1
        file_types[filetype] += 1
        sources[source] += 1
    
    # Display results
    print("🏷️  Source Types:")
    for source_type, count in source_types.most_common():
        percentage = (count / len(results['ids'])) * 100
        print(f"   {source_type:20s}: {count:4d} ({percentage:5.1f}%)")
    
    print("\n📑 Tags:")
    for tag, count in tags.most_common():
        percentage = (count / len(results['ids'])) * 100
        print(f"   {tag:20s}: {count:4d} ({percentage:5.1f}%)")
    
    print("\n📄 File Types:")
    for filetype, count in file_types.most_common(10):  # Show top 10
        percentage = (count / len(results['ids'])) * 100
        print(f"   {filetype:20s}: {count:4d} ({percentage:5.1f}%)")
    
    print("\n🌐 Sources:")
    for source, count in sources.most_common(10):  # Show top 10
        percentage = (count / len(results['ids'])) * 100
        # Truncate long URLs
        source_display = source[:50] + "..." if len(source) > 50 else source
        print(f"   {source_display:53s}: {count:4d} ({percentage:5.1f}%)")
    
    # Sample documents
    print("\n" + "=" * 80)
    print("📋 SAMPLE DOCUMENTS (First 5)")
    print("=" * 80)
    
    for i in range(min(5, len(results['ids']))):
        doc_id = results['ids'][i]
        metadata = results['metadatas'][i]
        content = results['documents'][i][:200] + "..." if len(results['documents'][i]) > 200 else results['documents'][i]
        
        print(f"\n[{i+1}] Document ID: {doc_id}")
        print(f"    Source Type: {metadata.get('source_type', 'N/A')}")
        print(f"    Tag: {metadata.get('tag', 'N/A')}")
        print(f"    File Type: {metadata.get('filetype', 'N/A')}")
        print(f"    Source: {metadata.get('source', 'N/A')[:100]}")
        print(f"    Content Preview: {content}")
    
    # Test retrieval
    print("\n" + "=" * 80)
    print("🔍 TEST RETRIEVAL")
    print("=" * 80)
    
    test_queries = [
        "CloudFuze migration",
        "SharePoint document",
        "pricing information",
    ]
    
    for query in test_queries:
        try:
            results = vectorstore.similarity_search(query, k=3)
            print(f"\nQuery: '{query}' → Found {len(results)} results")
            if results:
                for idx, doc in enumerate(results[:2], 1):
                    print(f"  [{idx}] {doc.metadata.get('source_type', 'N/A')} - {doc.metadata.get('tag', 'N/A')}")
                    print(f"      {doc.page_content[:150]}...")
        except Exception as e:
            print(f"Query: '{query}' → ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Vectorstore analysis complete!")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
