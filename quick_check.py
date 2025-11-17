import chromadb

client = chromadb.PersistentClient(path='./data/chroma_db')
coll = client.get_or_create_collection('cf_documents')
results = coll.get(limit=1000, include=['metadatas'])

blogs = sum(1 for m in results['metadatas'] if m.get('source_type') == 'web' or 'blog' in m.get('source', '').lower())
emails = sum(1 for m in results['metadatas'] if m.get('source_type') == 'email' or 'outlook' in m.get('source', '').lower())
sharepoint = sum(1 for m in results['metadatas'] if m.get('source_type') == 'sharepoint')

blog_urls = set(m.get('url') for m in results['metadatas'] if m.get('source_type') == 'web')
blog_urls = [u for u in blog_urls if u]

print(f"\nTotal chunks: {len(results['ids'])}")
print(f"SharePoint chunks: {sharepoint}")
print(f"Blog chunks: {blogs}")
print(f"Email chunks: {emails}")
print(f"\nUnique blog posts: {len(blog_urls)}")

if blog_urls:
    print("\nBlog URLs:")
    for url in sorted(blog_urls):
        print(f"  - {url}")

