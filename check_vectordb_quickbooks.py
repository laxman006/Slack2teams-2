#!/usr/bin/env python3
"""Check what information vectordb has about QuickBooks and CloudFuze Manage"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.vectorstore import vectorstore

if not vectorstore:
    print("❌ Vectorstore not initialized!")
    sys.exit(1)

print("=" * 80)
print("CHECKING VECTORDB FOR QUICKBOOKS + CLOUDFUZE MANAGE")
print("=" * 80)
print()

question = "Easily Manage Users in QuickBooks with CloudFuze Manage"
print(f"Question: {question}")
print()

# Search for documents
print("Searching vectordb...")
results = vectorstore.similarity_search_with_score(question, k=20)

print(f"\n✅ Found {len(results)} relevant documents\n")
print("=" * 80)
print("TOP 20 DOCUMENTS FROM VECTORDB:")
print("=" * 80)

for i, (doc, score) in enumerate(results, 1):
    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
    tag = metadata.get('tag', 'N/A')
    source_type = metadata.get('source_type', 'N/A')
    title = metadata.get('post_title', metadata.get('title', 'N/A'))
    url = metadata.get('url', metadata.get('source', 'N/A'))
    
    # Check for QuickBooks mentions
    content_lower = doc.page_content.lower()
    has_quickbooks = 'quickbooks' in content_lower
    has_cloudfuze_manage = 'cloudfuze manage' in content_lower or 'cloudfuze-manage' in content_lower
    has_user_management = 'user management' in content_lower or 'manage users' in content_lower
    
    print(f"\n[{i}] Score: {score:.4f}")
    print(f"    Tag: {tag}")
    print(f"    Source: {source_type}")
    print(f"    Title: {title[:80]}")
    print(f"    URL: {url[:80] if url != 'N/A' else 'N/A'}")
    print(f"    Keywords found: QuickBooks={has_quickbooks}, CloudFuze Manage={has_cloudfuze_manage}, User Management={has_user_management}")
    print(f"    Content preview: {doc.page_content[:150]}...")
    print("-" * 80)

# Summary
print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)

quickbooks_docs = sum(1 for doc, _ in results if 'quickbooks' in doc.page_content.lower())
cloudfuze_manage_docs = sum(1 for doc, _ in results if 'cloudfuze manage' in doc.page_content.lower() or 'cloudfuze-manage' in doc.page_content.lower())
user_mgmt_docs = sum(1 for doc, _ in results if 'user management' in doc.page_content.lower() or 'manage users' in doc.page_content.lower())

print(f"Documents mentioning 'QuickBooks': {quickbooks_docs}")
print(f"Documents mentioning 'CloudFuze Manage': {cloudfuze_manage_docs}")
print(f"Documents mentioning 'user management': {user_mgmt_docs}")
print(f"Total documents retrieved: {len(results)}")

