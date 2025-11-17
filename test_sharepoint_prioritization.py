#!/usr/bin/env python3
"""Test SharePoint prioritization"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.vectorstore import vectorstore
from app.endpoints import retrieve_with_branch_filter, classify_intent

if not vectorstore:
    print("❌ Vectorstore not initialized!")
    sys.exit(1)

print("=" * 80)
print("TESTING SHAREPOINT PRIORITIZATION")
print("=" * 80)
print()

question = "Easily Manage Users in QuickBooks with CloudFuze Manage"
print(f"Question: {question}\n")

# Get intent
intent_result = classify_intent(question)
intent = intent_result["intent"]

print(f"Intent: {intent}\n")

# Retrieve without prioritization (simulate old behavior)
print("=" * 80)
print("RETRIEVAL WITHOUT PRIORITIZATION (Old Behavior):")
print("=" * 80)

all_docs = vectorstore.similarity_search_with_score(question, k=50)
print(f"Retrieved {len(all_docs)} documents\n")

# Count sources
from collections import Counter
sources_before = Counter()
for doc, score in all_docs[:20]:
    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
    tag = metadata.get('tag', 'unknown')
    tag_prefix = tag.split('/')[0] if '/' in tag else tag
    sources_before[tag_prefix] += 1

print("Top 20 documents by source (BEFORE prioritization):")
for source, count in sources_before.most_common():
    print(f"  {source}: {count} documents")

# Now simulate prioritization
print("\n" + "=" * 80)
print("RETRIEVAL WITH PRIORITIZATION (New Behavior):")
print("=" * 80)

SHAREPOINT_BOOST = 0.6
EMAIL_BOOST = 0.8

boosted_docs = []
for doc, score in all_docs:
    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
    tag = metadata.get('tag', '').lower()
    source_type = metadata.get('source_type', '').lower()
    
    adjusted_score = score
    if 'sharepoint' in tag or source_type == 'sharepoint':
        adjusted_score = score * SHAREPOINT_BOOST
    elif 'email' in tag or source_type == 'email' or 'outlook' in tag:
        adjusted_score = score * EMAIL_BOOST
    
    boosted_docs.append((doc, adjusted_score))

# Re-sort
boosted_docs.sort(key=lambda x: x[1])

print(f"Retrieved {len(boosted_docs)} documents (after prioritization)\n")

# Count sources in top 20
sources_after = Counter()
for doc, score in boosted_docs[:20]:
    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
    tag = metadata.get('tag', 'unknown')
    tag_prefix = tag.split('/')[0] if '/' in tag else tag
    sources_after[tag_prefix] += 1

print("Top 20 documents by source (AFTER prioritization):")
for source, count in sources_after.most_common():
    print(f"  {source}: {count} documents")

# Show top 10 documents
print("\n" + "=" * 80)
print("TOP 10 DOCUMENTS AFTER PRIORITIZATION:")
print("=" * 80)

for i, (doc, score) in enumerate(boosted_docs[:10], 1):
    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
    tag = metadata.get('tag', 'N/A')
    source_type = metadata.get('source_type', 'N/A')
    title = metadata.get('post_title', metadata.get('title', 'N/A'))
    
    print(f"\n[{i}] Score: {score:.4f}")
    print(f"    Tag: {tag}")
    print(f"    Source: {source_type}")
    print(f"    Title: {title[:70]}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"Before: {dict(sources_before)}")
print(f"After:  {dict(sources_after)}")

sharepoint_before = sources_before.get('sharepoint', 0)
sharepoint_after = sources_after.get('sharepoint', 0)

if sharepoint_after > sharepoint_before:
    print(f"\n✅ SUCCESS: SharePoint documents increased from {sharepoint_before} to {sharepoint_after} in top 20!")
else:
    print(f"\n⚠️  Note: SharePoint documents: {sharepoint_before} → {sharepoint_after}")
    print("   (This is expected if no SharePoint docs match the query semantically)")

