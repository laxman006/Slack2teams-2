#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Source Connectivity Before Full Rebuild

This script tests connectivity to all three sources (blogs, SharePoint, Outlook)
with small samples, creates a temporary vectorstore, and tests query responses.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import traceback

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_BLOG_COUNT = 3
TEST_SHAREPOINT_COUNT = 5
TEST_EMAIL_COUNT = 5
TEST_VECTORSTORE_PATH = "./data/test_chroma_db"

# Results storage
test_results = {
    "timestamp": datetime.now().isoformat(),
    "blogs": {"status": "pending", "data": [], "error": None},
    "sharepoint": {"status": "pending", "data": [], "error": None},
    "outlook": {"status": "pending", "data": [], "error": None},
    "vectorstore": {"status": "pending", "stats": {}, "error": None},
    "queries": {"status": "pending", "results": [], "error": None}
}


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_subsection(title):
    """Print a formatted subsection header."""
    print(f"\n[{title}]")
    print("-" * 60)


# ============================================================================
# PHASE 1: Test Source Connectivity
# ============================================================================

def test_blog_connectivity():
    """Test fetching 3 blog posts from CloudFuze website."""
    print_subsection("PHASE 1.1: Testing Blog Connectivity")
    
    try:
        from app.helpers import fetch_posts
        
        # Use CloudFuze blog API URL
        blog_api_url = "https://cloudfuze.com/wp-json/wp/v2/posts"
        
        # Fetch limited posts for testing
        print(f"[*] Fetching {TEST_BLOG_COUNT} blog posts from WordPress API...")
        print(f"    URL: {blog_api_url}")
        
        posts = fetch_posts(blog_api_url, per_page=TEST_BLOG_COUNT, max_pages=1)
        
        if not posts:
            raise Exception("No blog posts returned from API")
        
        test_results["blogs"]["status"] = "success"
        test_results["blogs"]["data"] = []
        
        print(f"[OK] Successfully fetched {len(posts)} blog posts\n")
        
        for i, post in enumerate(posts[:TEST_BLOG_COUNT], 1):
            title = post.get('title', {}).get('rendered', 'No title')
            url = post.get('link', 'No URL')
            content = post.get('content', {}).get('rendered', '')
            word_count = len(content.split())
            
            post_info = {
                "title": title,
                "url": url,
                "word_count": word_count
            }
            test_results["blogs"]["data"].append(post_info)
            
            print(f"  [{i}] {title}")
            print(f"      URL: {url}")
            print(f"      Word count: {word_count}")
        
        return True, posts[:TEST_BLOG_COUNT]
        
    except Exception as e:
        print(f"[ERROR] Blog connectivity test failed: {e}")
        traceback.print_exc()
        test_results["blogs"]["status"] = "failed"
        test_results["blogs"]["error"] = str(e)
        return False, []


def test_sharepoint_connectivity():
    """Test extracting 5 files from SharePoint."""
    print_subsection("PHASE 1.2: Testing SharePoint Connectivity")
    
    try:
        from app.sharepoint_auth import sharepoint_auth
        from app.sharepoint_graph_extractor import SharePointGraphExtractor
        from config import SHAREPOINT_EXCLUDE_FOLDERS
        import os
        
        print("[*] Extracting sample SharePoint files...")
        print(f"[*] Target: {TEST_SHAREPOINT_COUNT} files for testing")
        
        # Get access token
        access_token = sharepoint_auth.get_access_token()
        
        # Get site ID from environment
        site_url = os.getenv("SHAREPOINT_SITE_URL", "")
        if ".sharepoint.com/sites/" in site_url:
            parts = site_url.replace("https://", "").replace("http://", "")
            hostname = parts.split("/")[0]
            site_path = "/" + "/".join(parts.split("/")[1:])
            site_id = f"{hostname}:{site_path}"
        else:
            raise Exception("Invalid SHAREPOINT_SITE_URL format")
        
        # Create extractor
        extractor = SharePointGraphExtractor(
            access_token=access_token,
            site_id=site_id,
            exclude_folders=SHAREPOINT_EXCLUDE_FOLDERS
        )
        
        # Extract limited files - get all but take only first N
        print("[*] Fetching file list from SharePoint...")
        all_docs = extractor.extract_all()
        
        if not all_docs:
            raise Exception("No SharePoint files extracted")
        
        # Take ONLY first N files for testing
        sample_docs = all_docs[:TEST_SHAREPOINT_COUNT]
        print(f"[OK] Taking first {len(sample_docs)} files from {len(all_docs)} total available")
        
        test_results["sharepoint"]["status"] = "success"
        test_results["sharepoint"]["data"] = []
        
        print(f"[OK] Successfully extracted {len(sample_docs)} SharePoint files\n")
        
        for i, doc in enumerate(sample_docs, 1):
            filename = doc.metadata.get('filename', 'Unknown')
            filetype = doc.metadata.get('filetype', 'unknown')
            file_path = doc.metadata.get('file_path', 'Unknown path')
            content_length = len(doc.page_content)
            
            file_info = {
                "filename": filename,
                "filetype": filetype,
                "path": file_path,
                "content_length": content_length
            }
            test_results["sharepoint"]["data"].append(file_info)
            
            print(f"  [{i}] {filename}")
            print(f"      Type: {filetype.upper()}")
            print(f"      Path: {file_path}")
            print(f"      Content length: {content_length} chars")
        
        return True, sample_docs
        
    except Exception as e:
        print(f"[ERROR] SharePoint connectivity test failed: {e}")
        traceback.print_exc()
        test_results["sharepoint"]["status"] = "failed"
        test_results["sharepoint"]["error"] = str(e)
        return False, []


def test_outlook_connectivity():
    """Test fetching 5 emails from Outlook."""
    print_subsection("PHASE 1.3: Testing Outlook Connectivity")
    
    try:
        from app.outlook_processor import OutlookProcessor
        from config import OUTLOOK_USER_EMAIL, OUTLOOK_FOLDER_NAME
        
        print(f"[*] Connecting to Outlook: {OUTLOOK_USER_EMAIL}")
        print(f"[*] Accessing folder: '{OUTLOOK_FOLDER_NAME}'")
        
        # Initialize Outlook processor
        processor = OutlookProcessor()
        
        # Fetch limited emails for testing
        print(f"[*] Fetching up to {TEST_EMAIL_COUNT} recent emails...")
        
        emails = processor.get_emails_from_folder(
            folder_name=OUTLOOK_FOLDER_NAME,
            max_emails=TEST_EMAIL_COUNT
        )
        
        if not emails:
            raise Exception("No emails retrieved")
        
        print(f"[OK] Retrieved {len(emails)} emails")
        
        # Group by conversation
        threads = processor.group_emails_by_conversation(emails)
        
        # Convert to documents (take first N threads)
        thread_docs = []
        for conv_id, thread in list(threads.items())[:TEST_EMAIL_COUNT]:
            doc = processor.format_thread_as_document(thread, OUTLOOK_FOLDER_NAME)
            if doc:
                thread_docs.append(doc)
        
        test_results["outlook"]["status"] = "success"
        test_results["outlook"]["data"] = []
        
        print(f"[OK] Successfully retrieved {len(emails)} emails in {len(thread_docs)} threads\n")
        
        for i, doc in enumerate(thread_docs[:TEST_EMAIL_COUNT], 1):
            subject = doc.metadata.get('subject', 'No subject')
            email_from = doc.metadata.get('email_from', 'Unknown')
            date = doc.metadata.get('date', 'Unknown')
            thread_id = doc.metadata.get('thread_id', 'No ID')
            
            email_info = {
                "subject": subject,
                "from": email_from,
                "date": date,
                "thread_id": thread_id
            }
            test_results["outlook"]["data"].append(email_info)
            
            print(f"  [{i}] {subject}")
            print(f"      From: {email_from}")
            print(f"      Date: {date}")
            print(f"      Thread ID: {thread_id[:20]}...")
        
        return True, thread_docs
        
    except Exception as e:
        print(f"[ERROR] Outlook connectivity test failed: {e}")
        traceback.print_exc()
        test_results["outlook"]["status"] = "failed"
        test_results["outlook"]["error"] = str(e)
        return False, []


# ============================================================================
# PHASE 2: Create Temporary Test Vectorstore
# ============================================================================

def create_test_vectorstore(blog_posts, sharepoint_docs, email_docs):
    """Create temporary vectorstore with sample data."""
    print_subsection("PHASE 2: Creating Temporary Test Vectorstore")
    
    try:
        import chromadb
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import Chroma
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document
        import tiktoken
        from config import OPENAI_API_KEY, CHUNK_TARGET_TOKENS, CHUNK_OVERLAP_TOKENS
        
        # Convert blog posts to documents
        print("[*] Converting blog posts to documents...")
        blog_docs = []
        for post in blog_posts:
            title = post.get('title', {}).get('rendered', 'No title')
            content = post.get('content', {}).get('rendered', '')
            url = post.get('link', '')
            
            # Strip HTML tags
            import re
            content = re.sub(r'<[^>]+>', '', content)
            
            doc = Document(
                page_content=content,
                metadata={
                    "source_type": "web",
                    "title": title,
                    "url": url,
                    "source": "cloudfuze_blog"
                }
            )
            blog_docs.append(doc)
        
        print(f"[OK] Created {len(blog_docs)} blog documents")
        
        # Combine all documents
        all_docs = blog_docs + sharepoint_docs + email_docs
        print(f"[*] Total documents to process: {len(all_docs)}")
        
        # Apply semantic chunking
        print("[*] Applying semantic chunking...")
        print(f"    Target: {CHUNK_TARGET_TOKENS} tokens per chunk")
        print(f"    Overlap: {CHUNK_OVERLAP_TOKENS} tokens")
        
        # Use token-based splitting
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
        def token_len(text):
            return len(encoding.encode(text))
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_TARGET_TOKENS * 4,  # Approximate chars
            chunk_overlap=CHUNK_OVERLAP_TOKENS * 4,
            length_function=token_len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = text_splitter.split_documents(all_docs)
        print(f"[OK] Created {len(chunks)} chunks")
        
        # Count by source
        chunk_counts = {"web": 0, "sharepoint": 0, "email": 0, "other": 0}
        for chunk in chunks:
            source_type = chunk.metadata.get("source_type", "other")
            chunk_counts[source_type] = chunk_counts.get(source_type, 0) + 1
        
        print(f"\n    Chunks by source:")
        for source, count in chunk_counts.items():
            print(f"      {source}: {count} chunks")
        
        # Create temporary vectorstore
        print(f"\n[*] Creating temporary vectorstore at: {TEST_VECTORSTORE_PATH}")
        
        # Initialize embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        
        # Create ChromaDB with HNSW indexing
        client = chromadb.PersistentClient(path=TEST_VECTORSTORE_PATH)
        
        # Delete collection if exists
        try:
            client.delete_collection("test_documents")
        except:
            pass
        
        collection = client.create_collection(
            name="test_documents",
            metadata={
                "hnsw:space": "cosine",
                "hnsw:M": 48,
                "hnsw:construction_ef": 200,
                "hnsw:search_ef": 100
            }
        )
        
        # Create vectorstore
        vectorstore = Chroma(
            client=client,
            collection_name="test_documents",
            embedding_function=embeddings
        )
        
        # Add documents
        print("[*] Generating embeddings and storing in vectorstore...")
        vectorstore.add_documents(chunks)
        
        print(f"[OK] Vectorstore created successfully!")
        print(f"    Path: {TEST_VECTORSTORE_PATH}")
        print(f"    Total chunks stored: {len(chunks)}")
        print(f"    HNSW indexing: Enabled (M=48, search_ef=100)")
        
        test_results["vectorstore"]["status"] = "success"
        test_results["vectorstore"]["stats"] = {
            "total_chunks": len(chunks),
            "chunks_by_source": chunk_counts,
            "path": TEST_VECTORSTORE_PATH
        }
        
        return True, vectorstore
        
    except Exception as e:
        print(f"[ERROR] Vectorstore creation failed: {e}")
        traceback.print_exc()
        test_results["vectorstore"]["status"] = "failed"
        test_results["vectorstore"]["error"] = str(e)
        return False, None


# ============================================================================
# PHASE 3: Test Query Responses
# ============================================================================

def test_query_responses(vectorstore):
    """Test 5 queries to verify retrieval works."""
    print_subsection("PHASE 3: Testing Query Responses")
    
    if not vectorstore:
        print("[ERROR] No vectorstore available for testing")
        test_results["queries"]["status"] = "failed"
        test_results["queries"]["error"] = "No vectorstore available"
        return False
    
    test_queries = [
        {
            "id": 1,
            "query": "What certifications does CloudFuze have?",
            "expected_source": "sharepoint",
            "description": "SharePoint query - should find certificates"
        },
        {
            "id": 2,
            "query": "Tell me about cloud migration",
            "expected_source": "web",
            "description": "Blog query - should find blog posts"
        },
        {
            "id": 3,
            "query": "What was discussed in recent emails?",
            "expected_source": "email",
            "description": "Email query - should find email threads"
        },
        {
            "id": 4,
            "query": "CloudFuze security and compliance",
            "expected_source": "mixed",
            "description": "Mixed query - should find multiple sources"
        },
        {
            "id": 5,
            "query": "Show me SOC 2 information",
            "expected_source": "sharepoint",
            "description": "Specific file query - should find SOC 2 docs"
        }
    ]
    
    try:
        query_results = []
        
        for test_query in test_queries:
            print(f"\n[Query {test_query['id']}] {test_query['query']}")
            print(f"  Expected: {test_query['expected_source']}")
            print(f"  Description: {test_query['description']}")
            
            # Retrieve using MMR
            results = vectorstore.max_marginal_relevance_search(
                test_query['query'],
                k=3,
                fetch_k=10
            )
            
            if not results:
                print("  [WARNING] No results found")
                query_results.append({
                    "query": test_query['query'],
                    "results_count": 0,
                    "results": []
                })
                continue
            
            print(f"  [OK] Found {len(results)} results:")
            
            result_list = []
            for i, doc in enumerate(results, 1):
                source_type = doc.metadata.get('source_type', 'unknown')
                title = doc.metadata.get('title') or doc.metadata.get('filename') or doc.metadata.get('subject', 'No title')
                snippet = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                
                result_info = {
                    "rank": i,
                    "source_type": source_type,
                    "title": title,
                    "snippet": snippet
                }
                result_list.append(result_info)
                
                print(f"    [{i}] Source: {source_type}")
                print(f"        Title: {title}")
                print(f"        Snippet: {snippet}")
            
            query_results.append({
                "query": test_query['query'],
                "expected_source": test_query['expected_source'],
                "results_count": len(results),
                "results": result_list
            })
        
        test_results["queries"]["status"] = "success"
        test_results["queries"]["results"] = query_results
        
        print(f"\n[OK] All {len(test_queries)} queries tested successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Query testing failed: {e}")
        traceback.print_exc()
        test_results["queries"]["status"] = "failed"
        test_results["queries"]["error"] = str(e)
        return False


# ============================================================================
# PHASE 4: Generate Test Report
# ============================================================================

def generate_report():
    """Generate TEST_CONNECTIVITY_REPORT.md."""
    print_subsection("PHASE 4: Generating Test Report")
    
    try:
        report_lines = []
        
        # Header
        report_lines.append("# Test Connectivity Report")
        report_lines.append(f"\n**Test Date:** {test_results['timestamp']}")
        report_lines.append("\n---\n")
        
        # Overall Status
        report_lines.append("## Overall Status\n")
        
        all_passed = (
            test_results["blogs"]["status"] == "success" and
            test_results["sharepoint"]["status"] == "success" and
            test_results["outlook"]["status"] == "success" and
            test_results["vectorstore"]["status"] == "success" and
            test_results["queries"]["status"] == "success"
        )
        
        if all_passed:
            report_lines.append("### ✓ ALL TESTS PASSED - Ready for Full Rebuild!\n")
        else:
            report_lines.append("### ✗ TESTS FAILED - Issues Found\n")
        
        # Connectivity Results
        report_lines.append("\n---\n")
        report_lines.append("## Connectivity Results\n")
        
        # Blogs
        status_icon = "✓" if test_results["blogs"]["status"] == "success" else "✗"
        report_lines.append(f"### {status_icon} Blogs")
        report_lines.append(f"**Status:** {test_results['blogs']['status']}")
        
        if test_results["blogs"]["status"] == "success":
            report_lines.append(f"\n**Posts Retrieved:** {len(test_results['blogs']['data'])}\n")
            for i, post in enumerate(test_results["blogs"]["data"], 1):
                report_lines.append(f"{i}. **{post['title']}**")
                report_lines.append(f"   - URL: {post['url']}")
                report_lines.append(f"   - Word count: {post['word_count']}\n")
        else:
            report_lines.append(f"\n**Error:** {test_results['blogs']['error']}\n")
        
        # SharePoint
        status_icon = "✓" if test_results["sharepoint"]["status"] == "success" else "✗"
        report_lines.append(f"\n### {status_icon} SharePoint")
        report_lines.append(f"**Status:** {test_results['sharepoint']['status']}")
        
        if test_results["sharepoint"]["status"] == "success":
            report_lines.append(f"\n**Files Retrieved:** {len(test_results['sharepoint']['data'])}\n")
            for i, file in enumerate(test_results["sharepoint"]["data"], 1):
                report_lines.append(f"{i}. **{file['filename']}**")
                report_lines.append(f"   - Type: {file['filetype'].upper()}")
                report_lines.append(f"   - Path: {file['path']}")
                report_lines.append(f"   - Content length: {file['content_length']} chars\n")
        else:
            report_lines.append(f"\n**Error:** {test_results['sharepoint']['error']}\n")
        
        # Outlook
        status_icon = "✓" if test_results["outlook"]["status"] == "success" else "✗"
        report_lines.append(f"\n### {status_icon} Outlook")
        report_lines.append(f"**Status:** {test_results['outlook']['status']}")
        
        if test_results["outlook"]["status"] == "success":
            report_lines.append(f"\n**Email Threads Retrieved:** {len(test_results['outlook']['data'])}\n")
            for i, email in enumerate(test_results["outlook"]["data"], 1):
                report_lines.append(f"{i}. **{email['subject']}**")
                report_lines.append(f"   - From: {email['from']}")
                report_lines.append(f"   - Date: {email['date']}")
                report_lines.append(f"   - Thread ID: {email['thread_id'][:30]}...\n")
        else:
            report_lines.append(f"\n**Error:** {test_results['outlook']['error']}\n")
        
        # Vectorstore Results
        report_lines.append("\n---\n")
        report_lines.append("## Vectorstore Test Results\n")
        
        status_icon = "✓" if test_results["vectorstore"]["status"] == "success" else "✗"
        report_lines.append(f"### {status_icon} Temporary Vectorstore Creation")
        report_lines.append(f"**Status:** {test_results['vectorstore']['status']}\n")
        
        if test_results["vectorstore"]["status"] == "success":
            stats = test_results["vectorstore"]["stats"]
            report_lines.append(f"**Total Chunks Created:** {stats['total_chunks']}")
            report_lines.append(f"**Storage Path:** `{stats['path']}`\n")
            report_lines.append("**Chunks by Source:**")
            for source, count in stats['chunks_by_source'].items():
                report_lines.append(f"- {source}: {count} chunks")
        else:
            report_lines.append(f"**Error:** {test_results['vectorstore']['error']}")
        
        # Query Test Results
        report_lines.append("\n---\n")
        report_lines.append("## Query Test Results\n")
        
        status_icon = "✓" if test_results["queries"]["status"] == "success" else "✗"
        report_lines.append(f"### {status_icon} Query Response Testing")
        report_lines.append(f"**Status:** {test_results['queries']['status']}\n")
        
        if test_results["queries"]["status"] == "success":
            for query_result in test_results["queries"]["results"]:
                report_lines.append(f"\n#### Query: \"{query_result['query']}\"")
                report_lines.append(f"**Expected Source:** {query_result['expected_source']}")
                report_lines.append(f"**Results Found:** {query_result['results_count']}\n")
                
                if query_result['results_count'] > 0:
                    report_lines.append("**Top Results:**")
                    for result in query_result['results']:
                        report_lines.append(f"\n{result['rank']}. **Source:** {result['source_type']}")
                        report_lines.append(f"   **Title:** {result['title']}")
                        report_lines.append(f"   **Snippet:** {result['snippet']}")
                else:
                    report_lines.append("*No results found*")
        else:
            report_lines.append(f"**Error:** {test_results['queries']['error']}")
        
        # Recommendation
        report_lines.append("\n---\n")
        report_lines.append("## Recommendation\n")
        
        if all_passed:
            report_lines.append("### ✓ READY FOR FULL REBUILD\n")
            report_lines.append("All connectivity tests passed successfully. You can proceed with full ingestion:\n")
            report_lines.append("1. Update your `.env` with full ingestion settings from `env_template_full_rebuild.txt`")
            report_lines.append("2. Ensure `INITIALIZE_VECTORSTORE=true`")
            report_lines.append("3. Fix `OUTLOOK_FOLDER_NAME=Sent Items` (with space)")
            report_lines.append("4. Run `python server.py`")
            report_lines.append("5. Monitor progress with `COMPLETE_REBUILD_CHECKLIST.md`")
            report_lines.append("\n**Expected Duration:** 1.5 - 2.5 hours")
            report_lines.append("\n**Expected Result:** 5,000 - 15,000+ document chunks")
        else:
            report_lines.append("### ✗ ISSUES FOUND - Fix Before Proceeding\n")
            report_lines.append("Some connectivity tests failed. Please review the errors above and fix:\n")
            
            if test_results["blogs"]["status"] != "success":
                report_lines.append(f"- **Blogs:** {test_results['blogs']['error']}")
            if test_results["sharepoint"]["status"] != "success":
                report_lines.append(f"- **SharePoint:** {test_results['sharepoint']['error']}")
            if test_results["outlook"]["status"] != "success":
                report_lines.append(f"- **Outlook:** {test_results['outlook']['error']}")
            
            report_lines.append("\nAfter fixing issues, re-run this test: `python test_source_connectivity.py`")
        
        report_lines.append("\n---\n")
        report_lines.append(f"\n*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # Write report
        report_content = "\n".join(report_lines)
        with open("TEST_CONNECTIVITY_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print("[OK] Report generated: TEST_CONNECTIVITY_REPORT.md")
        return True
        
    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}")
        traceback.print_exc()
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print_section("SOURCE CONNECTIVITY TEST")
    print(f"Testing: {TEST_BLOG_COUNT} blogs, {TEST_SHAREPOINT_COUNT} SharePoint files, {TEST_EMAIL_COUNT} emails")
    print(f"Temporary vectorstore: {TEST_VECTORSTORE_PATH}")
    
    # Phase 1: Test connectivity
    print_section("PHASE 1: Testing Source Connectivity")
    
    blog_success, blog_posts = test_blog_connectivity()
    sharepoint_success, sharepoint_docs = test_sharepoint_connectivity()
    outlook_success, email_docs = test_outlook_connectivity()
    
    # Summary
    print_subsection("Phase 1 Summary")
    print(f"  Blogs: {'✓ Success' if blog_success else '✗ Failed'}")
    print(f"  SharePoint: {'✓ Success' if sharepoint_success else '✗ Failed'}")
    print(f"  Outlook: {'✓ Success' if outlook_success else '✗ Failed'}")
    
    # Phase 2: Create vectorstore (only if Phase 1 succeeded)
    vectorstore = None
    if blog_success and sharepoint_success and outlook_success:
        print_section("PHASE 2: Creating Temporary Test Vectorstore")
        vectorstore_success, vectorstore = create_test_vectorstore(blog_posts, sharepoint_docs, email_docs)
    else:
        print_section("PHASE 2: SKIPPED (Phase 1 failed)")
        test_results["vectorstore"]["status"] = "skipped"
        test_results["vectorstore"]["error"] = "Phase 1 failed - connectivity issues"
        vectorstore_success = False
    
    # Phase 3: Test queries (only if Phase 2 succeeded)
    if vectorstore_success and vectorstore:
        print_section("PHASE 3: Testing Query Responses")
        query_success = test_query_responses(vectorstore)
    else:
        print_section("PHASE 3: SKIPPED (Phase 2 failed)")
        test_results["queries"]["status"] = "skipped"
        test_results["queries"]["error"] = "Phase 2 failed - no vectorstore"
        query_success = False
    
    # Phase 4: Generate report
    print_section("PHASE 4: Generating Test Report")
    generate_report()
    
    # Final summary
    print_section("TEST COMPLETE")
    
    all_passed = (
        blog_success and sharepoint_success and outlook_success and
        vectorstore_success and query_success
    )
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED!")
        print("\nYou can now proceed with full rebuild:")
        print("  1. Update .env with settings from env_template_full_rebuild.txt")
        print("  2. Run: python server.py")
        print("\nSee TEST_CONNECTIVITY_REPORT.md for details.")
    else:
        print("\n✗ TESTS FAILED")
        print("\nPlease review TEST_CONNECTIVITY_REPORT.md for errors and fix them.")
        print("Then re-run: python test_source_connectivity.py")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

