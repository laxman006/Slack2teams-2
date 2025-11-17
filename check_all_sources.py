#!/usr/bin/env python3
"""Check what sources are available in vectordb"""
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.vectorstore import vectorstore

if not vectorstore:
    print("❌ Vectorstore not initialized!")
    sys.exit(1)

print("=" * 80)
print("ANALYZING ALL SOURCES IN VECTORDB")
print("=" * 80)
print()

# Get all documents (sample)
print("Sampling documents from vectordb...")
# Search with a very generic query to get diverse results
results = vectorstore.similarity_search_with_score("cloud migration", k=100)

print(f"Analyzing {len(results)} documents...\n")

# Count sources
source_counts = Counter()
tag_counts = Counter()
source_type_counts = Counter()

for doc, score in results:
    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
    
    # Check different metadata fields
    tag = metadata.get('tag', 'unknown')
    source = metadata.get('source', 'unknown')
    source_type = metadata.get('source_type', 'unknown')
    
    # Count tags (first part before /)
    tag_prefix = tag.split('/')[0] if '/' in tag else tag
    tag_counts[tag_prefix] += 1
    
    # Count sources
    if source != 'unknown':
        source_counts[source] += 1
    
    # Count source types
    if source_type != 'unknown':
        source_type_counts[source_type] += 1

print("=" * 80)
print("TAG DISTRIBUTION (first part of tag):")
print("=" * 80)
for tag, count in tag_counts.most_common():
    print(f"  {tag}: {count} documents")

print("\n" + "=" * 80)
print("SOURCE DISTRIBUTION:")
print("=" * 80)
for source, count in source_counts.most_common():
    print(f"  {source}: {count} documents")

print("\n" + "=" * 80)
print("SOURCE TYPE DISTRIBUTION:")
print("=" * 80)
for source_type, count in source_type_counts.most_common():
    print(f"  {source_type}: {count} documents")

# Now check specifically for QuickBooks query
print("\n" + "=" * 80)
print("CHECKING QUICKBOOKS QUERY RETRIEVAL:")
print("=" * 80)

question = "Easily Manage Users in QuickBooks with CloudFuze Manage"
results_qb = vectorstore.similarity_search_with_score(question, k=50)

print(f"\nRetrieved {len(results_qb)} documents for QuickBooks query\n")

# Count sources in QuickBooks results
qb_source_counts = Counter()
qb_tag_counts = Counter()
qb_source_type_counts = Counter()

for doc, score in results_qb:
    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
    tag = metadata.get('tag', 'unknown')
    source = metadata.get('source', 'unknown')
    source_type = metadata.get('source_type', 'unknown')
    
    tag_prefix = tag.split('/')[0] if '/' in tag else tag
    qb_tag_counts[tag_prefix] += 1
    
    if source != 'unknown':
        qb_source_counts[source] += 1
    if source_type != 'unknown':
        qb_source_type_counts[source_type] += 1

print("Tag distribution in QuickBooks results:")
for tag, count in qb_tag_counts.most_common():
    print(f"  {tag}: {count} documents")

print("\nSource type distribution in QuickBooks results:")
for source_type, count in qb_source_type_counts.most_common():
    print(f"  {source_type}: {count} documents")

