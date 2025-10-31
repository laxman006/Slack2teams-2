"""
Compare embeddings between blog content and SharePoint content
"""
from pymongo import MongoClient
from config import MONGODB_URL, MONGODB_DATABASE, MONGODB_VECTORSTORE_COLLECTION
from dotenv import load_dotenv
import numpy as np

load_dotenv()

def compare_embeddings():
    """Compare embedding dimensions and types for blog vs SharePoint."""
    
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    collection = db[MONGODB_VECTORSTORE_COLLECTION]
    
    print("\n" + "="*80)
    print("COMPARING EMBEDDINGS: BLOG vs SHAREPOINT")
    print("="*80 + "\n")
    
    # Get a blog document
    blog_doc = collection.find_one({"metadata.source": "cloudfuze_blog"})
    
    # Get a SharePoint document
    sharepoint_doc = collection.find_one({"metadata.source": "cloudfuze_doc360"})
    
    if not blog_doc:
        print("❌ No blog documents found")
        return
    
    if not sharepoint_doc:
        print("❌ No SharePoint documents found")
        return
    
    print("✅ Found both blog and SharePoint documents\n")
    
    # Check embeddings
    blog_embedding = blog_doc.get('embedding')
    sharepoint_embedding = sharepoint_doc.get('embedding')
    
    print("BLOG CONTENT:")
    print(f"  Source: {blog_doc.get('metadata', {}).get('source')}")
    print(f"  Has embedding: {blog_embedding is not None}")
    if blog_embedding:
        print(f"  Embedding type: {type(blog_embedding)}")
        print(f"  Embedding dimensions: {len(blog_embedding)}")
        print(f"  First 5 values: {blog_embedding[:5]}")
    
    print("\nSHAREPOINT CONTENT:")
    print(f"  Source: {sharepoint_doc.get('metadata', {}).get('source')}")
    print(f"  Page title: {sharepoint_doc.get('metadata', {}).get('page_title', 'N/A')}")
    print(f"  Has embedding: {sharepoint_embedding is not None}")
    if sharepoint_embedding:
        print(f"  Embedding type: {type(sharepoint_embedding)}")
        print(f"  Embedding dimensions: {len(sharepoint_embedding)}")
        print(f"  First 5 values: {sharepoint_embedding[:5]}")
    
    # Compare
    print(f"\n{'='*80}")
    print("COMPARISON:")
    print(f"{'='*80}")
    
    if blog_embedding and sharepoint_embedding:
        if len(blog_embedding) == len(sharepoint_embedding):
            print(f"✅ SAME DIMENSIONS: Both use {len(blog_embedding)}-dimensional embeddings")
        else:
            print(f"❌ DIFFERENT DIMENSIONS:")
            print(f"   Blog: {len(blog_embedding)}")
            print(f"   SharePoint: {len(sharepoint_embedding)}")
        
        if type(blog_embedding) == type(sharepoint_embedding):
            print(f"✅ SAME TYPE: Both use {type(blog_embedding).__name__}")
        else:
            print(f"❌ DIFFERENT TYPES:")
            print(f"   Blog: {type(blog_embedding).__name__}")
            print(f"   SharePoint: {type(sharepoint_embedding).__name__}")
    
    # Check sample content
    print(f"\n{'='*80}")
    print("SAMPLE CONTENT:")
    print(f"{'='*80}")
    
    print("\nBlog content preview:")
    print(f"  {blog_doc.get('text', '')[:200]}...")
    
    print("\nSharePoint content preview:")
    print(f"  {sharepoint_doc.get('text', '')[:200]}...")
    
    # Count documents
    print(f"\n{'='*80}")
    print("DOCUMENT COUNTS:")
    print(f"{'='*80}")
    
    blog_count = collection.count_documents({"metadata.source": "cloudfuze_blog"})
    sharepoint_count = collection.count_documents({"metadata.source": "cloudfuze_doc360"})
    total_count = collection.count_documents({})
    
    print(f"  Blog documents: {blog_count}")
    print(f"  SharePoint documents: {sharepoint_count}")
    print(f"  Total documents: {total_count}")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    compare_embeddings()


