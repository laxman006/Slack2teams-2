"""
Check Vectorstore Content
=========================

Verifies if vectorstore contains relevant documents for specific queries.
This helps determine if retrieval issues are due to missing content or poor ranking.
"""

from app.vectorstore import vectorstore

def check_content_for_query(query: str, k: int = 10):
    """Check what documents exist for a specific query."""
    print(f"\n{'='*70}")
    print(f"QUERY: {query}")
    print('='*70)
    
    try:
        # Search vectorstore
        results = vectorstore.similarity_search(query, k=k)
        
        if not results:
            print("❌ NO DOCUMENTS FOUND")
            return False
        
        print(f"✅ Found {len(results)} documents\n")
        
        # Show each result
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get('source', 'Unknown')
            tag = doc.metadata.get('tag', 'unknown')
            content_preview = doc.page_content[:200].replace('\n', ' ')
            
            print(f"📄 Document #{i}")
            print(f"   Source: {source}")
            print(f"   Tag: {tag}")
            print(f"   Preview: {content_preview}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def check_keyword_presence(keywords: list):
    """Check if any documents contain specific keywords."""
    print(f"\n{'='*70}")
    print(f"KEYWORD SEARCH: {', '.join(keywords)}")
    print('='*70)
    
    try:
        # Search for each keyword
        all_docs = []
        for keyword in keywords:
            results = vectorstore.similarity_search(keyword, k=20)
            all_docs.extend(results)
        
        if not all_docs:
            print(f"❌ No documents found for any keyword")
            return False
        
        # Deduplicate
        seen_sources = set()
        unique_docs = []
        for doc in all_docs:
            source = doc.metadata.get('source', '')
            if source not in seen_sources:
                seen_sources.add(source)
                unique_docs.append(doc)
        
        print(f"✅ Found {len(unique_docs)} unique documents mentioning these keywords\n")
        
        # Show sources
        print("📚 Sources containing keywords:")
        for doc in unique_docs[:15]:  # Limit to top 15
            source = doc.metadata.get('source', 'Unknown')
            tag = doc.metadata.get('tag', 'unknown')
            
            # Check which keywords appear in content
            content_lower = doc.page_content.lower()
            found_keywords = [kw for kw in keywords if kw.lower() in content_lower]
            
            if found_keywords:
                print(f"   • {source}")
                print(f"     Tag: {tag}")
                print(f"     Contains: {', '.join(found_keywords)}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def analyze_vectorstore_coverage():
    """Analyze overall vectorstore content coverage."""
    print(f"\n{'='*70}")
    print("VECTORSTORE CONTENT ANALYSIS")
    print('='*70)
    
    try:
        # Get sample documents
        sample_docs = vectorstore.similarity_search("CloudFuze migration", k=50)
        
        if not sample_docs:
            print("❌ Vectorstore appears to be empty!")
            return False
        
        print(f"✅ Vectorstore contains documents ({len(sample_docs)} sampled)\n")
        
        # Analyze tags/sources
        tags = {}
        source_types = {}
        
        for doc in sample_docs:
            tag = doc.metadata.get('tag', 'unknown')
            source_type = doc.metadata.get('source_type', 'unknown')
            
            tags[tag] = tags.get(tag, 0) + 1
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        print("📊 Content by Tag:")
        for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {tag}: {count} documents")
        
        print("\n📊 Content by Source Type:")
        for source_type, count in sorted(source_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {source_type}: {count} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    print("\n🔍 CHECKING VECTORSTORE CONTENT FOR YOUR QUERIES\n")
    
    # Test the specific queries mentioned
    queries_to_test = [
        "Are migration logs available for OneDrive",
        "how does json slack to teams migration works",
        "CloudFuze migration features",
        "metadata permissions SharePoint OneDrive",
    ]
    
    print("="*70)
    print("TESTING SPECIFIC QUERIES")
    print("="*70)
    
    for query in queries_to_test:
        check_content_for_query(query, k=5)
    
    # Check for specific keywords
    print("\n" + "="*70)
    print("KEYWORD PRESENCE CHECK")
    print("="*70)
    
    keyword_sets = [
        ["migration logs", "onedrive", "audit"],
        ["json", "slack", "teams", "migration"],
        ["metadata", "permissions", "created by"],
    ]
    
    for keywords in keyword_sets:
        check_keyword_presence(keywords)
    
    # Overall analysis
    analyze_vectorstore_coverage()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("""
If documents were found:
  ✅ Your vectorstore has relevant content
  ✅ The keyword detection fix will help rank them better
  ✅ Answers should improve after rebuilding Docker

If no documents were found:
  ❌ Content may be missing from vectorstore
  ❌ You may need to rebuild vectorstore with correct sources
  ❌ Check if SharePoint/source documents contain this information
    """)
