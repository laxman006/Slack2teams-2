# -*- coding: utf-8 -*-
"""
Vectorstore Diagnostic Tool

Check what data sources are in the vectorstore.
"""

import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import CHROMA_DB_PATH
from collections import Counter

def check_vectorstore():
    """Check what's in the vectorstore."""
    print("=" * 60)
    print("VECTORSTORE DIAGNOSTIC")
    print("=" * 60)
    
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
        print(f"\n[*] Total documents: {total}")
        
        # Get all metadata
        all_docs = vectorstore._collection.get(include=['metadatas'])
        
        # Count by source type
        source_types = Counter()
        tags = Counter()
        
        for metadata in all_docs['metadatas']:
            source_type = metadata.get('source_type', 'unknown')
            tag = metadata.get('tag', 'unknown')
            source_types[source_type] += 1
            tags[tag] += 1
        
        print("\n[*] Documents by source type:")
        for source, count in source_types.most_common():
            print(f"    - {source}: {count} documents")
        
        print("\n[*] Documents by tag:")
        for tag, count in sorted(tags.items()):
            print(f"    - {tag}: {count} documents")
        
        # Check for Outlook specifically
        outlook_count = source_types.get('outlook', 0)
        email_tags = [tag for tag in tags.keys() if tag.startswith('email/')]
        
        print("\n" + "=" * 60)
        if outlook_count > 0:
            print(f"[✓] Found {outlook_count} Outlook email documents")
            print(f"    Email tags: {', '.join(email_tags)}")
        else:
            print("[!] NO Outlook email documents found!")
            print("    You need to run server with INITIALIZE_VECTORSTORE=true")
        print("=" * 60)
        
        # Test retrieval with email query
        print("\n[*] Testing email retrieval...")
        results = vectorstore.similarity_search("bugs raised by suraj", k=5)
        
        print(f"[*] Found {len(results)} results for 'bugs raised by suraj'")
        for idx, doc in enumerate(results, 1):
            source_type = doc.metadata.get('source_type', 'unknown')
            tag = doc.metadata.get('tag', 'unknown')
            print(f"    {idx}. source_type={source_type}, tag={tag}")
            print(f"       Preview: {doc.page_content[:100]}...")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_vectorstore()

