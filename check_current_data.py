#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick check of current vectorstore data"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from collections import Counter

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  CURRENT VECTORSTORE STATUS")
print("=" * 80)

try:
    import chromadb
    from config import CHROMA_DB_PATH
    
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection("langchain")
    
    total_count = collection.count()
    print(f"\n📊 Total Chunks: {total_count:,}")
    
    # Sample from different parts
    print("\n[*] Analyzing content...")
    
    # Get all source types by sampling
    samples = []
    sample_points = [0, 2000, 4000, 6000, 8000]
    
    for offset in sample_points:
        if offset < total_count:
            results = collection.get(offset=offset, limit=100, include=['metadatas'])
            if results and 'metadatas' in results:
                samples.extend(results['metadatas'])
    
    source_counts = Counter(m.get('source_type', 'unknown') for m in samples if m)
    
    print(f"\n📈 Source Distribution (from {len(samples)} samples):")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        percentage = (count / len(samples)) * 100
        estimated_total = int((count / len(samples)) * total_count)
        print(f"  {source.upper()}: ~{estimated_total:,} chunks ({percentage:.1f}% of sample)")
    
    # Detailed breakdown
    print("\n" + "=" * 80)
    print("  ESTIMATED BREAKDOWN")
    print("=" * 80)
    
    web_pct = source_counts.get('web', 0) / len(samples) if samples else 0
    sp_pct = source_counts.get('sharepoint', 0) / len(samples) if samples else 0
    email_pct = source_counts.get('outlook', 0) / len(samples) if samples else 0
    
    web_count = int(web_pct * total_count)
    sp_count = int(sp_pct * total_count)
    email_count = int(email_pct * total_count)
    
    print(f"\n📰 Blogs: {web_count:,} chunks")
    print(f"📁 SharePoint: {sp_count:,} chunks")
    print(f"📧 Emails: {email_count:,} chunks")
    print(f"\n{'─' * 40}")
    print(f"   TOTAL: {total_count:,} chunks")
    
    # Status
    print("\n" + "=" * 80)
    print("  STATUS")
    print("=" * 80)
    
    if email_count == 0:
        print("\n⚠️  NO EMAILS in vectorstore!")
        print("   Emails were removed but not re-added yet")
        print("\n   Next step: Add emails back with correct date filter")
    elif email_count < 500:
        print(f"\n⚠️  Only {email_count} email chunks")
        print("   This seems low - may need to add more")
    else:
        print(f"\n✅ {email_count} email chunks present")
    
    print(f"\n✅ Blogs: {'Present' if web_count > 1000 else 'Missing/Incomplete'}")
    print(f"✅ SharePoint: {'Present' if sp_count > 1000 else 'Missing/Incomplete'}")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

