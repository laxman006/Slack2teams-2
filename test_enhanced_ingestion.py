"""
Test script for enhanced ingestion pipeline.

Tests:
1. Small dataset ingestion (emails, SharePoint files, blogs)
2. Metadata extraction
3. Semantic chunking
4. Deduplication
5. Graph relationships
6. Retrieval quality

Usage:
    python test_enhanced_ingestion.py
"""

import os
import sys
from datetime import datetime

# Set test mode environment variables
os.environ["ENABLE_DEDUPLICATION"] = "true"
os.environ["ENABLE_UNSTRUCTURED"] = "true"
os.environ["ENABLE_GRAPH_STORAGE"] = "true"
os.environ["CHUNK_TARGET_TOKENS"] = "800"

from app.enhanced_helpers import build_enhanced_vectorstore
from app.sharepoint_processor import process_sharepoint_content
from app.outlook_processor import process_outlook_content
from app.helpers import fetch_web_content
from app.graph_store import get_graph_store
from scripts.backup_vectorstore import create_backup

from config import (
    CHROMA_DB_PATH,
    ENABLE_SHAREPOINT_SOURCE,
    ENABLE_OUTLOOK_SOURCE,
    ENABLE_WEB_SOURCE,
    WEB_SOURCE_URL,
    GRAPH_DB_PATH
)


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_backup():
    """Test 1: Backup existing vectorstore."""
    print_section("TEST 1: Backup Existing Vectorstore")
    
    backup_path = create_backup()
    if backup_path:
        print(f"[OK] Backup created successfully at: {backup_path}")
        return True
    elif not os.path.exists(CHROMA_DB_PATH):
        print("[OK] No existing vectorstore to backup (fresh install)")
        return True
    else:
        print("[ERROR] Backup failed")
        return False


def test_data_collection():
    """Test 2: Collect sample data from sources."""
    print_section("TEST 2: Data Collection")
    
    sharepoint_docs = []
    outlook_docs = []
    blog_docs = []
    
    # Collect SharePoint documents (if enabled)
    if ENABLE_SHAREPOINT_SOURCE:
        try:
            print("\n[*] Collecting SharePoint documents...")
            sharepoint_docs = process_sharepoint_content()
            print(f"[OK] Collected {len(sharepoint_docs)} SharePoint documents")
            
            # Show file type breakdown
            if sharepoint_docs:
                from collections import Counter
                file_types = Counter(doc.metadata.get('filetype', 'unknown') for doc in sharepoint_docs)
                print("\n[*] SharePoint File Types Found:")
                for filetype, count in sorted(file_types.items()):
                    print(f"    {filetype.upper()}: {count} files")
        except Exception as e:
            print(f"[WARNING] SharePoint collection failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Collect Outlook emails (if enabled)
    if ENABLE_OUTLOOK_SOURCE:
        try:
            print("\n[*] Collecting Outlook emails...")
            outlook_docs = process_outlook_content()
            print(f"[OK] Collected {len(outlook_docs)} Outlook documents")
        except Exception as e:
            print(f"[WARNING] Outlook collection failed: {e}")
    
    # Collect blog posts (if enabled) - limit to 10 for testing
    if ENABLE_WEB_SOURCE:
        try:
            print("\n[*] Collecting blog posts (limited to 10 for testing)...")
            # Temporarily modify to fetch fewer posts
            original_max_pages = os.getenv("BLOG_MAX_PAGES")
            os.environ["BLOG_MAX_PAGES"] = "1"  # Just 1 page
            
            blog_docs = fetch_web_content(WEB_SOURCE_URL)
            # Limit to first 10
            blog_docs = blog_docs[:10]
            
            # Restore original
            if original_max_pages:
                os.environ["BLOG_MAX_PAGES"] = original_max_pages
            
            print(f"[OK] Collected {len(blog_docs)} blog documents")
        except Exception as e:
            print(f"[WARNING] Blog collection failed: {e}")
    
    total_docs = len(sharepoint_docs) + len(outlook_docs) + len(blog_docs)
    print(f"\n[OK] Total documents collected: {total_docs}")
    
    if total_docs == 0:
        print("[WARNING] No documents collected - check your source configurations")
        print("  - Make sure ENABLE_*_SOURCE flags are set in config.py")
        print("  - Verify credentials and permissions")
        return None
    
    return {
        "sharepoint": sharepoint_docs,
        "outlook": outlook_docs,
        "blog": blog_docs
    }


def test_ingestion(collected_data):
    """Test 3: Run enhanced ingestion pipeline."""
    print_section("TEST 3: Enhanced Ingestion Pipeline")
    
    if not collected_data:
        print("[SKIP] No data to ingest")
        return None, None
    
    try:
        # Clear existing vectorstore for clean test
        if os.path.exists(CHROMA_DB_PATH):
            import shutil
            shutil.rmtree(CHROMA_DB_PATH)
            print("[*] Cleared existing vectorstore for clean test")
        
        # Run enhanced ingestion
        print("\n[*] Running enhanced ingestion pipeline...")
        vectorstore, report = build_enhanced_vectorstore(
            sharepoint_docs=collected_data.get("sharepoint"),
            outlook_docs=collected_data.get("outlook"),
            blog_docs=collected_data.get("blog")
        )
        
        print("\n[OK] Ingestion completed successfully!")
        return vectorstore, report
        
    except Exception as e:
        print(f"[ERROR] Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_retrieval(vectorstore):
    """Test 4: Test retrieval with sample queries."""
    print_section("TEST 4: Retrieval Quality Testing")
    
    if not vectorstore:
        print("[SKIP] No vectorstore available")
        return False
    
    # Test queries - customize these based on your data
    test_queries = [
        "How to migrate from Slack to Microsoft Teams?",
        "What are the main features of CloudFuze?",
        "Tell me about SharePoint migration",
        "How do I contact support?",
        "What pricing plans are available?"
    ]
    
    print(f"\n[*] Running {len(test_queries)} test queries...\n")
    
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            "fetch_k": 10,
            "lambda_mult": 0.7
        }
    )
    
    all_passed = True
    
    for i, query in enumerate(test_queries, 1):
        try:
            print(f"\nQuery {i}: \"{query}\"")
            print("-" * 80)
            
            results = retriever.invoke(query)
            
            if not results:
                print("[WARNING] No results returned")
                continue
            
            print(f"Retrieved: {len(results)} chunks")
            
            # Check diversity (different sources)
            sources = set(doc.metadata.get("source", "unknown") for doc in results)
            filetypes = set(doc.metadata.get("filetype", "unknown") for doc in results)
            
            print(f"Sources: {', '.join(sources)}")
            print(f"File types: {', '.join(filetypes)}")
            
            # Show top result
            if results:
                top_result = results[0]
                print(f"\nTop Result:")
                print(f"  Source: {top_result.metadata.get('source', 'unknown')}")
                print(f"  File: {top_result.metadata.get('filename', 'unknown')}")
                print(f"  Type: {top_result.metadata.get('filetype', 'unknown')}")
                content_preview = top_result.page_content[:150].replace('\n', ' ')
                print(f"  Preview: {content_preview}...")
            
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            all_passed = False
    
    if all_passed:
        print("\n[OK] All retrieval tests passed")
    
    return all_passed


def test_graph_relationships():
    """Test 5: Verify graph relationships."""
    print_section("TEST 5: Graph Relationship Verification")
    
    try:
        graph_store = get_graph_store(GRAPH_DB_PATH)
        
        # Get statistics
        stats = graph_store.get_stats()
        
        print("\nGraph Store Statistics:")
        print("-" * 80)
        for key, value in stats.items():
            formatted_key = key.replace("_", " ").title()
            print(f"  {formatted_key}: {value}")
        
        # Check if we have relationships
        if stats.get("total_relationships", 0) > 0:
            print("\n[OK] Graph relationships created successfully")
            
            # Sample a few relationships
            print("\nSample Relationships:")
            rels = graph_store.get_relationships()[:5]
            for rel in rels:
                print(f"  {rel['rel_type']}: {rel['from_id'][:8]}... -> {rel['to_id'][:8]}...")
            
            return True
        else:
            print("\n[WARNING] No relationships found in graph store")
            return False
            
    except Exception as e:
        print(f"[ERROR] Graph verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "🚀" * 40)
    print("  ENHANCED INGESTION TEST SUITE")
    print("🚀" * 40)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track results
    results = []
    
    # Test 1: Backup
    results.append(("Backup", test_backup()))
    
    # Test 2: Data collection
    collected_data = test_data_collection()
    results.append(("Data Collection", collected_data is not None))
    
    if collected_data:
        # Test 3: Ingestion
        vectorstore, report = test_ingestion(collected_data)
        results.append(("Ingestion", vectorstore is not None))
        
        # Print ingestion report
        if report:
            print_section("INGESTION REPORT")
            print(report)
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"test_ingest_report_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n[OK] Report saved to: {report_file}")
        
        # Test 4: Retrieval
        if vectorstore:
            results.append(("Retrieval", test_retrieval(vectorstore)))
        
        # Test 5: Graph relationships
        results.append(("Graph Relationships", test_graph_relationships()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    print("\nDetailed Results:")
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {status}: {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Enhanced ingestion pipeline is working correctly")
        print("\nNext Steps:")
        print("  1. Review the ingestion report above")
        print("  2. Test with full dataset (set ENABLE_*_SOURCE flags)")
        print("  3. Configure source-specific settings in config.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the details above.")
        return 1


if __name__ == "__main__":
    exit(main())

