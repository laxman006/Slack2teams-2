import chromadb

print("\nChecking BACKUP vectorstore (from today)...")
client = chromadb.PersistentClient(path='./data/backups/chroma_db_backup_20251112_150150')
try:
    coll = client.get_or_create_collection('cf_documents')
    results = coll.get(limit=1000, include=['metadatas'])
    
    blogs = sum(1 for m in results['metadatas'] if m.get('source_type') == 'web' or 'blog' in m.get('source', '').lower())
    emails = sum(1 for m in results['metadatas'] if m.get('source_type') == 'email' or 'outlook' in m.get('source', '').lower())
    sharepoint = sum(1 for m in results['metadatas'] if m.get('source_type') == 'sharepoint')
    
    print(f"Total chunks: {len(results['ids'])}")
    print(f"SharePoint chunks: {sharepoint}")
    print(f"Blog chunks: {blogs}")
    print(f"Email chunks: {emails}")
except Exception as e:
    print(f"Error: {e}")

print("\nChecking OLD BACKUP vectorstore (from Nov 1)...")
client2 = chromadb.PersistentClient(path='./data/chroma_db_backup_20251101_155650')
try:
    coll2 = client2.get_or_create_collection('cf_documents')
    results2 = coll2.get(limit=1000, include=['metadatas'])
    
    blogs2 = sum(1 for m in results2['metadatas'] if m.get('source_type') == 'web' or 'blog' in m.get('source', '').lower())
    emails2 = sum(1 for m in results2['metadatas'] if m.get('source_type') == 'email' or 'outlook' in m.get('source', '').lower())
    sharepoint2 = sum(1 for m in results2['metadatas'] if m.get('source_type') == 'sharepoint')
    
    blog_urls = set(m.get('url') for m in results2['metadatas'] if m.get('source_type') == 'web')
    blog_urls = [u for u in blog_urls if u]
    
    print(f"Total chunks: {len(results2['ids'])}")
    print(f"SharePoint chunks: {sharepoint2}")
    print(f"Blog chunks: {blogs2}")
    print(f"Email chunks: {emails2}")
    print(f"Unique blog posts: {len(blog_urls)}")
    
    if blog_urls:
        print("\nBlog URLs:")
        for url in sorted(blog_urls)[:5]:
            print(f"  - {url}")
except Exception as e:
    print(f"Error: {e}")

