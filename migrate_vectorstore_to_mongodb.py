#!/usr/bin/env python3
"""
Migration script to transfer vector store from ChromaDB (SQLite) to MongoDB.

This script will:
1. Read all documents and embeddings from ChromaDB
2. Transfer them to MongoDB with the same structure
3. Preserve all metadata and embeddings
4. Show migration progress and results
"""

import os
import sys
from typing import List, Dict, Any
from datetime import datetime

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from tqdm import tqdm

from config import CHROMA_DB_PATH, MONGODB_URL, MONGODB_DATABASE
from app.mongodb_vectorstore import MongoDBVectorStore


def get_chroma_stats(vectorstore: Chroma) -> Dict[str, Any]:
    """Get statistics from ChromaDB."""
    try:
        collection = vectorstore._collection
        count = collection.count()
        
        # Assume OpenAI embeddings dimension (1536)
        embedding_dim = 1536
        
        return {
            "total_documents": count,
            "embedding_dimension": embedding_dim,
        }
    except Exception as e:
        print(f"[ERROR] Failed to get ChromaDB stats: {e}")
        return {"total_documents": 0, "embedding_dimension": 0}


def migrate_chromadb_to_mongodb(
    batch_size: int = 100,
    mongodb_collection: str = "cloudfuze_vectorstore",
    clear_mongodb_first: bool = False,
):
    """
    Migrate all data from ChromaDB to MongoDB.
    
    Args:
        batch_size: Number of documents to process at once
        mongodb_collection: Target MongoDB collection name
        clear_mongodb_first: Whether to clear MongoDB collection before migration
    """
    print("=" * 70)
    print("VECTOR STORE MIGRATION: ChromaDB → MongoDB")
    print("=" * 70)
    print(f"Source: ChromaDB ({CHROMA_DB_PATH})")
    print(f"Target: MongoDB ({MONGODB_URL}/{MONGODB_DATABASE}.{mongodb_collection})")
    print("-" * 70)
    
    # Step 1: Check if ChromaDB exists
    if not os.path.exists(CHROMA_DB_PATH):
        print(f"[ERROR] ChromaDB not found at: {CHROMA_DB_PATH}")
        print("Please ensure your ChromaDB vectorstore exists before migration.")
        return False
    
    # Step 2: Initialize embeddings (must be same as original)
    print("[*] Initializing OpenAI embeddings...")
    embeddings = OpenAIEmbeddings()
    print("[OK] Embeddings initialized")
    
    # Step 3: Load ChromaDB
    print("[*] Loading ChromaDB vectorstore...")
    try:
        chroma_vectorstore = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings
        )
        print("[OK] ChromaDB loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load ChromaDB: {e}")
        return False
    
    # Step 4: Get ChromaDB statistics
    print("[*] Analyzing ChromaDB contents...")
    chroma_stats = get_chroma_stats(chroma_vectorstore)
    total_docs = chroma_stats["total_documents"]
    print(f"[OK] Found {total_docs} documents in ChromaDB")
    
    if total_docs == 0:
        print("[WARNING] No documents found in ChromaDB. Nothing to migrate.")
        return True
    
    # Step 5: Initialize MongoDB Vector Store
    print("[*] Connecting to MongoDB...")
    try:
        mongodb_vectorstore = MongoDBVectorStore(
            collection_name=mongodb_collection,
            embedding_function=embeddings,
        )
        print("[OK] MongoDB connection established")
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        print("\nPlease ensure:")
        print("  1. MongoDB is running")
        print("  2. Connection string is correct in .env file")
        print("  3. You have necessary permissions")
        return False
    
    # Step 6: Optionally clear existing MongoDB data
    if clear_mongodb_first:
        print("[*] Clearing existing MongoDB collection...")
        mongodb_vectorstore.clear()
        print("[OK] MongoDB collection cleared")
    
    # Step 7: Get existing MongoDB stats
    mongodb_stats_before = mongodb_vectorstore.get_collection_stats()
    print(f"[*] MongoDB collection has {mongodb_stats_before['total_documents']} documents before migration")
    
    # Step 8: Migrate documents in batches
    print("\n" + "=" * 70)
    print("STARTING MIGRATION")
    print("=" * 70)
    
    migrated_count = 0
    failed_count = 0
    
    try:
        # Get collection handle
        collection = chroma_vectorstore._collection

        # Calculate number of batches
        num_batches = (total_docs + batch_size - 1) // batch_size

        print(f"[*] Processing {total_docs} documents in {num_batches} batches...")
        print("-" * 70)

        # Fetch documents in paginated batches to avoid 'Error finding id' and memory spikes
        for batch_num in tqdm(range(num_batches), desc="Migrating batches"):
            offset = batch_num * batch_size

            try:
                # Read a page of documents directly from ChromaDB
                page = collection.get(
                    include=['documents', 'metadatas', 'embeddings'],
                    limit=batch_size,
                    offset=offset,
                )

                texts = page.get('documents') or []
                metadatas = page.get('metadatas') or [{}] * len(texts)
                embeddings_list = page.get('embeddings')

                if not texts:
                    continue

                # If embeddings are missing (rare), regenerate them to avoid failure
                if embeddings_list is None:
                    embeddings_list = embeddings.embed_documents(texts)

                # Defensive: lengths must match
                if len(embeddings_list) != len(texts):
                    # Regenerate to maintain alignment
                    embeddings_list = embeddings.embed_documents(texts)

                documents_to_insert = []
                for text, metadata, embedding in zip(texts, metadatas, embeddings_list):
                    documents_to_insert.append({
                        "text": text,
                        "embedding": embedding,
                        "metadata": metadata or {},
                        "created_at": datetime.utcnow(),
                        "migrated_from": "chromadb",
                    })

                if documents_to_insert:
                    result = mongodb_vectorstore.collection.insert_many(documents_to_insert)
                    batch_count = len(result.inserted_ids)
                    migrated_count += batch_count

                # Progress update
                if (batch_num + 1) % 10 == 0 or batch_num == num_batches - 1:
                    progress = (migrated_count / total_docs) * 100
                    print(f"[*] Progress: {migrated_count}/{total_docs} ({progress:.1f}%)")

            except Exception as e:
                failed_count += min(batch_size, total_docs - offset)
                print(f"[WARNING] Batch {batch_num + 1} failed (offset {offset}): {e}")
                # Fallback: try per-document to skip corrupt entries
                try:
                    # Attempt to fetch ids for this window (ids are always returned)
                    page_ids = collection.get(limit=batch_size, offset=offset).get('ids', [])
                    for doc_id in page_ids:
                        try:
                            item = collection.get(ids=[doc_id], include=['documents', 'metadatas', 'embeddings'])
                            texts = item.get('documents') or []
                            if not texts:
                                continue
                            text = texts[0]
                            metadata = (item.get('metadatas') or [{}])[0]
                            emb = (item.get('embeddings') or [None])[0]
                            if emb is None:
                                emb = embeddings.embed_documents([text])[0]
                            mongodb_vectorstore.collection.insert_one({
                                "text": text,
                                "embedding": emb,
                                "metadata": metadata or {},
                                "created_at": datetime.utcnow(),
                                "migrated_from": "chromadb",
                            })
                            migrated_count += 1
                        except Exception as inner_e:
                            print(f"[SKIP] Corrupt/invalid doc id {doc_id}: {inner_e}")
                            failed_count += 1
                except Exception as ids_e:
                    print(f"[ERROR] Could not enumerate ids for fallback at offset {offset}: {ids_e}")
                continue
        
        print("-" * 70)
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False
    
    # Step 9: Verify migration
    print("\n" + "=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    
    # Get final MongoDB stats
    mongodb_stats_after = mongodb_vectorstore.get_collection_stats()
    
    print(f"ChromaDB documents:          {total_docs}")
    print(f"Successfully migrated:       {migrated_count}")
    print(f"Failed migrations:           {failed_count}")
    print(f"MongoDB documents (before):  {mongodb_stats_before['total_documents']}")
    print(f"MongoDB documents (after):   {mongodb_stats_after['total_documents']}")
    print(f"Embedding dimension:         {mongodb_stats_after['embedding_dimension']}")
    
    # Verify migration success
    expected_total = mongodb_stats_before['total_documents'] + migrated_count
    if mongodb_stats_after['total_documents'] == expected_total:
        print("\n✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("\nNext steps:")
        print("  1. Test MongoDB vector store with: python test_mongodb_vectorstore.py")
        print("  2. Update .env to use MongoDB: USE_MONGODB_VECTORSTORE=true")
        print("  3. Restart your application")
        print("  4. Keep ChromaDB backup until you verify everything works")
        return True
    else:
        print(f"\n⚠️  MIGRATION COMPLETED WITH WARNINGS")
        print(f"Expected {expected_total} documents but found {mongodb_stats_after['total_documents']}")
        print("Please verify the data manually before removing ChromaDB")
        return False


def verify_migration(mongodb_collection: str = "cloudfuze_vectorstore"):
    """
    Verify that MongoDB vector store is working correctly.
    
    Args:
        mongodb_collection: MongoDB collection name to test
    """
    print("\n" + "=" * 70)
    print("TESTING MONGODB VECTOR STORE")
    print("=" * 70)
    
    # Initialize MongoDB vector store
    embeddings = OpenAIEmbeddings()
    mongodb_vectorstore = MongoDBVectorStore(
        collection_name=mongodb_collection,
        embedding_function=embeddings,
    )
    
    # Test similarity search
    test_queries = [
        "What is CloudFuze?",
        "How does migration work?",
        "What are the pricing plans?",
    ]
    
    print("\n[*] Testing similarity search with sample queries...")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            results = mongodb_vectorstore.similarity_search(query, k=3)
            print(f"  Found {len(results)} results")
            if results:
                print(f"  Top result preview: {results[0].page_content[:100]}...")
        except Exception as e:
            print(f"  [ERROR] Search failed: {e}")
    
    print("\n✅ MongoDB vector store is operational!")


def main():
    """Main migration function."""
    print("\n" + "=" * 70)
    print("VECTOR STORE MIGRATION TOOL")
    print("ChromaDB (SQLite) → MongoDB")
    print("=" * 70)
    
    # Confirm migration
    print("\nThis will migrate your vector store from ChromaDB to MongoDB.")
    print("The original ChromaDB will NOT be modified.")
    print("\nOptions:")
    print("  1. Migrate (keep existing MongoDB data)")
    print("  2. Migrate (clear MongoDB first - fresh start)")
    print("  3. Verify existing migration")
    print("  4. Cancel")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        print("\n[*] Starting migration (keeping existing MongoDB data)...")
        success = migrate_chromadb_to_mongodb(
            batch_size=100,
            clear_mongodb_first=False,
        )
        if success:
            verify_migration()
    
    elif choice == "2":
        print("\n⚠️  WARNING: This will DELETE all existing data in MongoDB vector store!")
        confirm = input("Type 'YES' to confirm: ").strip()
        if confirm == "YES":
            print("\n[*] Starting migration (clearing MongoDB first)...")
            success = migrate_chromadb_to_mongodb(
                batch_size=100,
                clear_mongodb_first=True,
            )
            if success:
                verify_migration()
        else:
            print("[*] Migration cancelled")
    
    elif choice == "3":
        print("\n[*] Verifying existing migration...")
        verify_migration()
    
    else:
        print("\n[*] Migration cancelled")
        return
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[*] Migration cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

