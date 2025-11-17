#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check vectorstore rebuild progress
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  CHECKING REBUILD PROGRESS")
print("=" * 80)

try:
    import chromadb
    from config import CHROMA_DB_PATH
    
    print(f"\nVectorstore path: {CHROMA_DB_PATH}")
    
    # Check if vectorstore exists and has data
    if os.path.exists(CHROMA_DB_PATH):
        print("[✓] Vectorstore directory exists")
        
        try:
            client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            collections = client.list_collections()
            
            if collections:
                print(f"[✓] Found {len(collections)} collection(s)")
                
                for collection in collections:
                    count = collection.count()
                    print(f"\n  Collection: {collection.name}")
                    print(f"  Document chunks: {count}")
                    
                    if count > 0:
                        # Try to peek at some documents
                        try:
                            results = collection.peek(limit=5)
                            if results and 'metadatas' in results:
                                metadatas = results['metadatas']
                                
                                # Count by source type
                                from collections import Counter
                                source_types = [m.get('source_type', 'unknown') for m in metadatas if m]
                                source_counts = Counter(source_types)
                                
                                print(f"  Sample sources found:")
                                for source, count in source_counts.items():
                                    print(f"    - {source}: {count} samples")
                        except Exception as e:
                            print(f"  [Note] Could not peek: {e}")
            else:
                print("[!] No collections found yet - rebuild may be in progress")
        except Exception as e:
            print(f"[!] Could not access vectorstore: {e}")
            print("    Rebuild may be in progress...")
    else:
        print("[!] Vectorstore directory does not exist yet")
        print("    Rebuild is starting...")
    
    # Check graph database
    from config import GRAPH_DB_PATH
    if os.path.exists(GRAPH_DB_PATH):
        print(f"\n[✓] Graph database exists: {GRAPH_DB_PATH}")
        
        import sqlite3
        try:
            conn = sqlite3.connect(GRAPH_DB_PATH)
            cursor = conn.cursor()
            
            # Check documents table
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            print(f"  Documents in graph: {doc_count}")
            
            # Check chunks table
            cursor.execute("SELECT COUNT(*) FROM chunks")
            chunk_count = cursor.fetchone()[0]
            print(f"  Chunks in graph: {chunk_count}")
            
            conn.close()
        except Exception as e:
            print(f"  [Note] Could not read graph database: {e}")
    else:
        print(f"\n[!] Graph database not created yet: {GRAPH_DB_PATH}")
    
    print("\n" + "=" * 80)
    print("To monitor real-time progress, check the server output logs")
    print("The rebuild will take 1.5-2.5 hours depending on data size")
    print("=" * 80)
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

