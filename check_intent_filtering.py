#!/usr/bin/env python3
"""Check how intent classification affects document retrieval"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.endpoints import classify_intent, retrieve_with_branch_filter, INTENT_BRANCHES
from app.vectorstore import vectorstore

if not vectorstore:
    print("❌ Vectorstore not initialized!")
    sys.exit(1)

question = "Easily Manage Users in QuickBooks with CloudFuze Manage"

print("=" * 80)
print("INTENT CLASSIFICATION ANALYSIS")
print("=" * 80)
print(f"\nQuestion: {question}\n")

# Check intent classification
intent_result = classify_intent(question)
intent = intent_result["intent"]
intent_confidence = intent_result["confidence"]
intent_method = intent_result.get("method", "unknown")

print(f"Classified Intent: {intent}")
print(f"Confidence: {intent_confidence:.2f}")
print(f"Method: {intent_method}")

# Check branch configuration
branch_config = INTENT_BRANCHES.get(intent, INTENT_BRANCHES["other"])
print(f"\nBranch Config for '{intent}':")
print(f"  Description: {branch_config.get('description', 'N/A')}")
print(f"  Include Tags: {branch_config.get('include_tags', [])}")
print(f"  Exclude Keywords: {branch_config.get('exclude_keywords', [])}")

# Check ENABLE_INTENT_CLASSIFICATION
from app.endpoints import ENABLE_INTENT_CLASSIFICATION
print(f"\nENABLE_INTENT_CLASSIFICATION: {ENABLE_INTENT_CLASSIFICATION}")

# Now check what happens with retrieval
print("\n" + "=" * 80)
print("RETRIEVAL WITH INTENT FILTERING:")
print("=" * 80)

if ENABLE_INTENT_CLASSIFICATION:
    doc_results = retrieve_with_branch_filter(
        query=question,
        intent=intent,
        k=50
    )
    print(f"\nRetrieved {len(doc_results)} documents with intent filtering")
else:
    # Direct retrieval without intent filtering
    all_docs = vectorstore.similarity_search_with_score(question, k=50)
    doc_results = all_docs
    print(f"\nRetrieved {len(doc_results)} documents WITHOUT intent filtering (direct search)")

# Analyze sources
from collections import Counter
tag_counts = Counter()
source_type_counts = Counter()

for doc, score in doc_results:
    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
    tag = metadata.get('tag', 'unknown')
    source_type = metadata.get('source_type', 'unknown')
    
    tag_prefix = tag.split('/')[0] if '/' in tag else tag
    tag_counts[tag_prefix] += 1
    source_type_counts[source_type] += 1

print("\nTag distribution:")
for tag, count in tag_counts.most_common():
    print(f"  {tag}: {count} documents")

print("\nSource type distribution:")
for source_type, count in source_type_counts.most_common():
    print(f"  {source_type}: {count} documents")

# Check if include_tags is filtering out other sources
if branch_config.get('include_tags'):
    print(f"\n⚠️  WARNING: Branch config has 'include_tags': {branch_config.get('include_tags')}")
    print("   This means ONLY documents with these tags will be included!")
    print("   Documents from other sources (SharePoint, emails) will be EXCLUDED if their tags don't match.")

