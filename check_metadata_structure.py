#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check actual metadata structure"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import json

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  METADATA STRUCTURE CHECK")
print("=" * 80)

try:
    import chromadb
    from config import CHROMA_DB_PATH
    
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection("langchain")
    
    # Get sample from each source type
    results = collection.get(limit=100, include=['metadatas'])
    
    if results and 'metadatas' in results:
        metadatas = results['metadatas']
        
        # Find one of each type
        web_sample = None
        sp_sample = None
        email_sample = None
        
        for m in metadatas:
            if m:
                source_type = m.get('source_type', '')
                if source_type == 'web' and not web_sample:
                    web_sample = m
                elif source_type == 'sharepoint' and not sp_sample:
                    sp_sample = m
                elif source_type in ['email', 'outlook'] and not email_sample:
                    email_sample = m
        
        print("\n📰 BLOG METADATA SAMPLE:")
        if web_sample:
            print(json.dumps(web_sample, indent=2))
        else:
            print("  No blog metadata found")
        
        print("\n📁 SHAREPOINT METADATA SAMPLE:")
        if sp_sample:
            print(json.dumps(sp_sample, indent=2))
        else:
            print("  No SharePoint metadata found")
        
        print("\n📧 EMAIL METADATA SAMPLE:")
        if email_sample:
            print(json.dumps(email_sample, indent=2))
        else:
            print("  No email metadata found")
        
        # Count by actual source_type
        from collections import Counter
        source_types = Counter(m.get('source_type', 'unknown') for m in metadatas if m)
        
        print("\n" + "=" * 80)
        print("SOURCE TYPE DISTRIBUTION (sample of 100):")
        for stype, count in source_types.items():
            print(f"  {stype}: {count}")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

