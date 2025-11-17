#!/usr/bin/env python3
"""Check the actual distribution of all documents in vectordb"""
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.vectorstore import vectorstore

if not vectorstore:
    print("❌ Vectorstore not initialized!")
    sys.exit(1)

print("=" * 80)
print("FULL VECTORDB DISTRIBUTION ANALYSIS")
print("=" * 80)
print()

# Get ALL documents from the collection
print("Fetching all documents from vectordb...")
collection = vectorstore._collection

# Get all IDs
all_ids = collection.get()['ids']
print(f"Total documents in vectordb: {len(all_ids)}")

# Sample a larger set to get better distribution
print("\nSampling documents to analyze distribution...")
sample_size = min(1000, len(all_ids))
sample_ids = all_ids[:sample_size]

# Get metadata for sampled documents
results = collection.get(ids=sample_ids, include=['metadatas'])

tag_counts = Counter()
source_type_counts = Counter()
source_counts = Counter()

for metadata in results.get('metadatas', []):
    if not metadata:
        continue
    
    tag = metadata.get('tag', 'unknown')
    source = metadata.get('source', 'unknown')
    source_type = metadata.get('source_type', 'unknown')
    
    # Get tag prefix (first part before /)
    tag_prefix = tag.split('/')[0] if '/' in tag else tag
    tag_counts[tag_prefix] += 1
    
    if source != 'unknown':
        source_counts[source] += 1
    if source_type != 'unknown':
        source_type_counts[source_type] += 1

print(f"\nAnalyzed {len(results.get('metadatas', []))} documents from sample")
print("=" * 80)
print("TAG DISTRIBUTION (sample):")
print("=" * 80)
for tag, count in tag_counts.most_common():
    percentage = (count / len(results.get('metadatas', []))) * 100
    print(f"  {tag}: {count} documents ({percentage:.1f}%)")

print("\n" + "=" * 80)
print("SOURCE TYPE DISTRIBUTION (sample):")
print("=" * 80)
for source_type, count in source_type_counts.most_common():
    percentage = (count / len(results.get('metadatas', []))) * 100
    print(f"  {source_type}: {count} documents ({percentage:.1f}%)")

print("\n" + "=" * 80)
print("SOURCE DISTRIBUTION (sample):")
print("=" * 80)
for source, count in source_counts.most_common(10):
    percentage = (count / len(results.get('metadatas', []))) * 100
    print(f"  {source}: {count} documents ({percentage:.1f}%)")

# Now check why QuickBooks query only returns blogs
print("\n" + "=" * 80)
print("WHY QUICKBOOKS QUERY RETURNS ONLY BLOGS:")
print("=" * 80)

question = "Easily Manage Users in QuickBooks with CloudFuze Manage"
print(f"\nQuery: {question}")

# Get top 100 results
all_results = vectorstore.similarity_search_with_score(question, k=100)

print(f"\nTop 100 results by source type:")
result_source_types = Counter()
result_tags = Counter()

for doc, score in all_results:
    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
    tag = metadata.get('tag', 'unknown')
    source_type = metadata.get('source_type', 'unknown')
    
    tag_prefix = tag.split('/')[0] if '/' in tag else tag
    result_tags[tag_prefix] += 1
    result_source_types[source_type] += 1

print("\nTag distribution in top 100 results:")
for tag, count in result_tags.most_common():
    print(f"  {tag}: {count} documents")

print("\nSource type distribution in top 100 results:")
for source_type, count in result_source_types.most_common():
    print(f"  {source_type}: {count} documents")

# Check if there are any SharePoint/email docs in the top 100
sharepoint_in_top100 = result_tags.get('sharepoint', 0)
email_in_top100 = result_tags.get('email', 0)

print(f"\n📊 Summary:")
print(f"  SharePoint documents in top 100: {sharepoint_in_top100}")
print(f"  Email documents in top 100: {email_in_top100}")
print(f"  Blog documents in top 100: {result_tags.get('blog', 0)}")

if sharepoint_in_top100 == 0 and email_in_top100 == 0:
    print("\n⚠️  REASON: Semantic similarity search is finding blog documents as most relevant")
    print("   This is because:")
    print("   1. Blog documents likely have better semantic embeddings for this query")
    print("   2. Blog documents may be more similar in content/topic to 'user management'")
    print("   3. The query is about 'CloudFuze Manage' which is heavily covered in blogs")

