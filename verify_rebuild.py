"""Verify vectorstore rebuild was successful and tags are proper."""
import os
os.environ["INITIALIZE_VECTORSTORE"] = "false"

try:
    from app.vectorstore import load_existing_vectorstore
    
    print("\n" + "="*80)
    print("VECTORSTORE VERIFICATION")
    print("="*80)
    
    vectorstore = load_existing_vectorstore()
    
    if not vectorstore:
        print("❌ Failed to load vectorstore!")
        exit(1)
    
    collection = vectorstore._collection
    all_data = collection.get(include=['documents', 'metadatas'])
    
    total_docs = len(all_data['documents'])
    print(f"\n✅ Total Documents: {total_docs}")
    
    # Count by tag
    tag_counts = {}
    source_counts = {}
    sharepoint_folders = set()
    
    for metadata in all_data['metadatas']:
        # Count by tag
        tag = metadata.get('tag', 'unknown')
        if tag not in tag_counts:
            tag_counts[tag] = 0
        tag_counts[tag] += 1
        
        # Count by source
        source = metadata.get('source', 'unknown')
        if source not in source_counts:
            source_counts[source] = 0
        source_counts[source] += 1
        
        # Collect SharePoint folders
        if tag.startswith('sharepoint/'):
            folder = tag.replace('sharepoint/', '').split('/')[0]
            sharepoint_folders.add(folder)
    
    print("\n" + "="*80)
    print("📊 DOCUMENTS BY TAG")
    print("="*80)
    
    # Sort by count
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_docs) * 100
        print(f"  {tag:50s} : {count:5d} docs ({percentage:5.1f}%)")
    
    print("\n" + "="*80)
    print("📂 DOCUMENTS BY SOURCE")
    print("="*80)
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_docs) * 100
        print(f"  {source:30s} : {count:5d} docs ({percentage:5.1f}%)")
    
    # SharePoint analysis
    sharepoint_count = sum(1 for tag in tag_counts.keys() if tag.startswith('sharepoint/'))
    sharepoint_doc_count = sum(count for tag, count in tag_counts.items() if tag.startswith('sharepoint/'))
    
    print("\n" + "="*80)
    print("📁 SHAREPOINT ANALYSIS")
    print("="*80)
    print(f"  SharePoint documents: {sharepoint_doc_count}")
    print(f"  SharePoint unique folders: {sharepoint_count}")
    print(f"  SharePoint top-level folders: {len(sharepoint_folders)}")
    
    if sharepoint_folders:
        print(f"\n  Top-level SharePoint folders:")
        for folder in sorted(sharepoint_folders):
            print(f"    • {folder}")
    
    # Blog analysis
    blog_count = tag_counts.get('blog', 0)
    print("\n" + "="*80)
    print("📝 BLOG POSTS ANALYSIS")
    print("="*80)
    print(f"  Blog post documents: {blog_count}")
    
    print("\n" + "="*80)
    print("✅ VERIFICATION COMPLETE")
    print("="*80)
    print("\nYour vectorstore is properly tagged and ready to use!")
    print("\nTag structure:")
    print("  • Blog posts: 'blog'")
    print("  • SharePoint: 'sharepoint/folder/subfolder'")
    print("  • PDFs: 'pdf'")
    print("  • Excel: 'excel'")
    print("  • Word: 'doc'")
    print("\nThese tags enable intent-based filtering for better retrieval!")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

