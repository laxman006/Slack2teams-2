"""
Comprehensive Vectorstore Verification Tool
Checks what was fetched, what's stored, and identifies any gaps.
"""
import os
os.environ["INITIALIZE_VECTORSTORE"] = "false"

import json
import requests
from datetime import datetime

print("="*100)
print("COMPREHENSIVE VECTORSTORE VERIFICATION")
print("="*100)
print()

# ============================================================================
# PART 1: Check What SHOULD Be Fetched (Source Analysis)
# ============================================================================
print("📊 PART 1: SOURCE ANALYSIS - What should be fetched?")
print("="*100)

# Check blog posts from WordPress API
print("\n[1] Checking CloudFuze Blog Posts...")
try:
    # Get total posts from WordPress API
    response = requests.get(
        "https://cloudfuze.com/wp-json/wp/v2/posts?per_page=1&page=1",
        timeout=10
    )
    total_posts = int(response.headers.get('X-WP-Total', 0))
    total_pages = int(response.headers.get('X-WP-TotalPages', 0))
    
    print(f"   ✓ Total blog posts available: {total_posts}")
    print(f"   ✓ Total pages (100 posts/page): {total_pages}")
    print(f"   ✓ Expected chunks: ~{total_posts * 10} (avg 10 chunks per post)")
except Exception as e:
    print(f"   ✗ Error checking blog: {e}")
    total_posts = 0
    total_pages = 0

# Check SharePoint (can't check without authentication)
print("\n[2] Checking SharePoint...")
print("   ℹ SharePoint content varies - checking what's in vectorstore")

# ============================================================================
# PART 2: Check What IS Stored (Vectorstore Analysis)
# ============================================================================
print("\n\n📦 PART 2: VECTORSTORE ANALYSIS - What is actually stored?")
print("="*100)

try:
    from app.vectorstore import vectorstore
    
    if not vectorstore:
        print("\n✗ Vectorstore not loaded!")
        print("  Run 'python rebuild_now.py' first")
        exit(1)
    
    print("\n✓ Vectorstore loaded successfully")
    
    # Get all documents
    collection = vectorstore._collection
    all_data = collection.get(include=['documents', 'metadatas'])
    
    total_docs = len(all_data['documents'])
    print(f"\n📊 Total Documents in Vectorstore: {total_docs:,}")
    
    # Analyze by source
    print("\n" + "="*100)
    print("DOCUMENTS BY SOURCE")
    print("="*100)
    
    blog_docs = []
    sharepoint_docs = []
    other_docs = []
    
    blog_posts_unique = set()
    sharepoint_files_unique = set()
    sharepoint_folders = set()
    
    for doc_text, metadata in zip(all_data['documents'], all_data['metadatas']):
        tag = metadata.get('tag', 'unknown')
        source = metadata.get('source', 'unknown')
        
        if tag == 'blog':
            blog_docs.append(metadata)
            post_title = metadata.get('post_title', '')
            if post_title:
                blog_posts_unique.add(post_title)
        elif tag.startswith('sharepoint'):
            sharepoint_docs.append(metadata)
            file_name = metadata.get('file_name', '')
            if file_name:
                sharepoint_files_unique.add(file_name)
            # Extract folder
            folder_parts = tag.split('/')
            if len(folder_parts) > 1:
                sharepoint_folders.add(folder_parts[1])  # First folder level
        else:
            other_docs.append(metadata)
    
    # Blog statistics
    print(f"\n📝 BLOG POSTS:")
    print(f"   Total chunks: {len(blog_docs):,}")
    print(f"   Unique posts: {len(blog_posts_unique):,}")
    print(f"   Avg chunks/post: {len(blog_docs) / max(len(blog_posts_unique), 1):.1f}")
    
    if total_posts > 0:
        coverage = (len(blog_posts_unique) / total_posts) * 100
        print(f"   Coverage: {coverage:.1f}% ({len(blog_posts_unique)}/{total_posts})")
        
        if coverage < 95:
            print(f"   ⚠️  WARNING: Only {coverage:.1f}% of blog posts fetched!")
            print(f"   Missing: ~{total_posts - len(blog_posts_unique)} posts")
        else:
            print(f"   ✓ Excellent coverage!")
    
    # SharePoint statistics
    print(f"\n📁 SHAREPOINT DOCUMENTS:")
    print(f"   Total chunks: {len(sharepoint_docs):,}")
    print(f"   Unique files: {len(sharepoint_files_unique):,}")
    print(f"   Avg chunks/file: {len(sharepoint_docs) / max(len(sharepoint_files_unique), 1):.1f}")
    print(f"   Top-level folders: {len(sharepoint_folders)}")
    
    if sharepoint_folders:
        print(f"\n   Folders indexed:")
        for folder in sorted(sharepoint_folders):
            folder_docs = [d for d in sharepoint_docs if d.get('tag', '').startswith(f'sharepoint/{folder}')]
            print(f"      • {folder}: {len(folder_docs)} chunks")
    
    # Other sources
    if other_docs:
        print(f"\n📄 OTHER SOURCES:")
        print(f"   Total chunks: {len(other_docs):,}")
    
    # ========================================================================
    # PART 3: Content Type Analysis
    # ========================================================================
    print("\n\n" + "="*100)
    print("CONTENT TYPE ANALYSIS")
    print("="*100)
    
    # Check for different file types in SharePoint
    file_types = {}
    for metadata in sharepoint_docs:
        file_name = metadata.get('file_name', '')
        if '.' in file_name:
            ext = file_name.split('.')[-1].lower()
            if ext not in file_types:
                file_types[ext] = 0
            file_types[ext] += 1
    
    if file_types:
        print("\nSharePoint file types:")
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   • .{ext}: {count} files")
    
    # ========================================================================
    # PART 4: Image Handling Explanation
    # ========================================================================
    print("\n\n" + "="*100)
    print("🖼️  IMAGE HANDLING")
    print("="*100)
    
    print("\n⚠️  IMPORTANT: Images are NOT stored in the vectorstore")
    print("\nHow images are handled:")
    print("   • Blog posts: Images removed, only text extracted")
    print("   • SharePoint: Image files not processed, only text documents")
    print("   • Why: Vectorstores store TEXT embeddings, not images")
    print("   • Images can't be converted to text embeddings")
    print("\nWhat IS stored:")
    print("   ✓ Text content from blog posts")
    print("   ✓ Text content from SharePoint documents")
    print("   ✓ Metadata (URLs, titles, file names)")
    print("   ✓ Links to original content (includes images)")
    print("\nTo view images:")
    print("   • Blog post links stored in metadata (post_url)")
    print("   • SharePoint file links stored in metadata (file_url)")
    print("   • Users can click links to see full content with images")
    
    # ========================================================================
    # PART 5: Missing Content Detection
    # ========================================================================
    print("\n\n" + "="*100)
    print("🔍 MISSING CONTENT DETECTION")
    print("="*100)
    
    issues = []
    
    # Check blog coverage
    if total_posts > 0:
        if len(blog_posts_unique) < total_posts * 0.95:
            issues.append(f"Only {len(blog_posts_unique)}/{total_posts} blog posts fetched")
    
    # Check if SharePoint is empty
    if len(sharepoint_docs) == 0:
        issues.append("No SharePoint documents found (check ENABLE_SHAREPOINT_SOURCE)")
    
    # Check if very few SharePoint docs
    if 0 < len(sharepoint_docs) < 100:
        issues.append(f"Only {len(sharepoint_docs)} SharePoint chunks (might be incomplete)")
    
    if issues:
        print("\n⚠️  POTENTIAL ISSUES:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("\n✓ No issues detected - vectorstore looks complete!")
    
    # ========================================================================
    # PART 6: Sample Documents
    # ========================================================================
    print("\n\n" + "="*100)
    print("📋 SAMPLE DOCUMENTS (First 5)")
    print("="*100)
    
    sample_docs = list(zip(all_data['documents'][:5], all_data['metadatas'][:5]))
    
    for i, (doc_text, metadata) in enumerate(sample_docs, 1):
        tag = metadata.get('tag', 'unknown')
        source = metadata.get('source', 'unknown')
        title = metadata.get('post_title', metadata.get('file_name', 'N/A'))
        
        print(f"\n[{i}] Tag: {tag}")
        print(f"    Source: {source}")
        print(f"    Title: {title[:60]}...")
        print(f"    Content: {doc_text[:100]}...")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n\n" + "="*100)
    print("✅ VERIFICATION SUMMARY")
    print("="*100)
    
    print(f"\n📊 Total Documents: {total_docs:,}")
    print(f"   • Blog posts: {len(blog_docs):,} chunks from {len(blog_posts_unique):,} posts")
    print(f"   • SharePoint: {len(sharepoint_docs):,} chunks from {len(sharepoint_files_unique):,} files")
    if other_docs:
        print(f"   • Other: {len(other_docs):,} chunks")
    
    print(f"\n🎯 Status: ", end="")
    if not issues:
        print("✓ COMPLETE - Vectorstore is fully populated")
    else:
        print(f"⚠️  INCOMPLETE - {len(issues)} issue(s) found")
    
    print("\n🖼️  Images: NOT stored (text-only vectorstore)")
    print("    → Original content with images accessible via stored URLs")
    
    print("\n" + "="*100)

except Exception as e:
    print(f"\n✗ Error loading vectorstore: {e}")
    print("\nIf you see corruption errors, run:")
    print("  python rebuild_now.py")
    import traceback
    traceback.print_exc()


