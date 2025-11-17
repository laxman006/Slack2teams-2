#!/usr/bin/env python3
"""Check if SharePoint or email documents mention QuickBooks or CloudFuze Manage"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.vectorstore import vectorstore

if not vectorstore:
    print("❌ Vectorstore not initialized!")
    sys.exit(1)

print("=" * 80)
print("CHECKING SHAREPOINT & EMAIL DOCUMENTS FOR QUICKBOOKS/CLOUDFUZE MANAGE")
print("=" * 80)
print()

# Get collection
collection = vectorstore._collection

# Get all documents
all_data = collection.get(include=['metadatas', 'documents'])

print(f"Total documents: {len(all_data['ids'])}")

# Filter for SharePoint and email documents
sharepoint_docs = []
email_docs = []

for i, metadata in enumerate(all_data.get('metadatas', [])):
    if not metadata:
        continue
    
    tag = metadata.get('tag', '').lower()
    source_type = metadata.get('source_type', '').lower()
    doc_content = all_data.get('documents', [])[i] if i < len(all_data.get('documents', [])) else ''
    
    if 'sharepoint' in tag or source_type == 'sharepoint':
        sharepoint_docs.append({
            'tag': tag,
            'source_type': source_type,
            'title': metadata.get('title', metadata.get('post_title', 'N/A')),
            'content': doc_content[:200] if doc_content else 'N/A'
        })
    elif 'email' in tag or source_type == 'email' or 'outlook' in tag:
        email_docs.append({
            'tag': tag,
            'source_type': source_type,
            'title': metadata.get('title', metadata.get('post_title', 'N/A')),
            'content': doc_content[:200] if doc_content else 'N/A'
        })

print(f"\nSharePoint documents found: {len(sharepoint_docs)}")
print(f"Email documents found: {len(email_docs)}")

# Check for QuickBooks mentions
print("\n" + "=" * 80)
print("CHECKING FOR QUICKBOOKS MENTIONS:")
print("=" * 80)

sharepoint_quickbooks = []
email_quickbooks = []

for doc in sharepoint_docs:
    content_lower = doc['content'].lower()
    if 'quickbooks' in content_lower:
        sharepoint_quickbooks.append(doc)

for doc in email_docs:
    content_lower = doc['content'].lower()
    if 'quickbooks' in content_lower:
        email_quickbooks.append(doc)

print(f"\nSharePoint documents mentioning 'QuickBooks': {len(sharepoint_quickbooks)}")
print(f"Email documents mentioning 'QuickBooks': {len(email_quickbooks)}")

# Check for CloudFuze Manage mentions
print("\n" + "=" * 80)
print("CHECKING FOR CLOUDFUZE MANAGE MENTIONS:")
print("=" * 80)

sharepoint_manage = []
email_manage = []

for doc in sharepoint_docs:
    content_lower = doc['content'].lower()
    if 'cloudfuze manage' in content_lower or 'cloudfuze-manage' in content_lower:
        sharepoint_manage.append(doc)

for doc in email_docs:
    content_lower = doc['content'].lower()
    if 'cloudfuze manage' in content_lower or 'cloudfuze-manage' in content_lower:
        email_manage.append(doc)

print(f"\nSharePoint documents mentioning 'CloudFuze Manage': {len(sharepoint_manage)}")
print(f"Email documents mentioning 'CloudFuze Manage': {len(email_manage)}")

# Show samples
if sharepoint_manage:
    print("\n" + "=" * 80)
    print("SAMPLE SHAREPOINT DOCUMENTS WITH CLOUDFUZE MANAGE:")
    print("=" * 80)
    for i, doc in enumerate(sharepoint_manage[:5], 1):
        print(f"\n[{i}] {doc['title']}")
        print(f"    Tag: {doc['tag']}")
        print(f"    Content preview: {doc['content']}...")

if email_manage:
    print("\n" + "=" * 80)
    print("SAMPLE EMAIL DOCUMENTS WITH CLOUDFUZE MANAGE:")
    print("=" * 80)
    for i, doc in enumerate(email_manage[:5], 1):
        print(f"\n[{i}] {doc['title']}")
        print(f"    Tag: {doc['tag']}")
        print(f"    Content preview: {doc['content']}...")

# Summary
print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"Total SharePoint documents: {len(sharepoint_docs)}")
print(f"Total Email documents: {len(email_docs)}")
print(f"SharePoint docs with QuickBooks: {len(sharepoint_quickbooks)}")
print(f"Email docs with QuickBooks: {len(email_quickbooks)}")
print(f"SharePoint docs with CloudFuze Manage: {len(sharepoint_manage)}")
print(f"Email docs with CloudFuze Manage: {len(email_manage)}")

if len(sharepoint_manage) == 0 and len(email_manage) == 0:
    print("\n💡 CONCLUSION:")
    print("   SharePoint and email documents don't contain 'CloudFuze Manage' content")
    print("   This is why semantic search returns only blog documents - they're the only")
    print("   source that has relevant content about CloudFuze Manage and user management.")

