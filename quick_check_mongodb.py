"""
Quick MongoDB Vector Store Check - Run anytime to verify
"""
import sys
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

print("\n" + "🔍 QUICK MONGODB VECTOR STORE CHECK" + "\n" + "=" * 50)

# 1. Config check
from config import VECTORSTORE_BACKEND
print(f"\n✓ Config: VECTORSTORE_BACKEND = '{VECTORSTORE_BACKEND}'")

# 2. Load vectorstore
from app.vectorstore import vectorstore
if vectorstore:
    vectorstore_type = type(vectorstore).__name__
    print(f"✓ Loaded: {vectorstore_type}")
    
    if "MongoDB" in vectorstore_type:
        print("✅ CONFIRMED: Using MongoDB as knowledge base!")
        
        if hasattr(vectorstore, 'get_collection_stats'):
            stats = vectorstore.get_collection_stats()
            print(f"\n📊 Stats:")
            print(f"   • Database: {stats['database_name']}")
            print(f"   • Collection: {stats['collection_name']}")
            print(f"   • Documents: {stats['total_documents']:,}")
            print(f"   • Embedding dim: {stats['embedding_dimension']}")
    elif "Chroma" in vectorstore_type:
        print("❌ WARNING: Using ChromaDB, not MongoDB!")
    else:
        print(f"⚠️  Unknown type: {vectorstore_type}")
else:
    print("❌ Vectorstore not loaded")

print("\n" + "=" * 50 + "\n")

