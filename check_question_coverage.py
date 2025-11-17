"""
Check if vectorstore has content for specific user questions.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from config import PERSIST_DIRECTORY

# Initialize vectorstore
print("\n" + "="*70)
print("  CHECKING VECTORSTORE COVERAGE FOR USER QUESTIONS")
print("="*70 + "\n")

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vectorstore = Chroma(
    persist_directory=PERSIST_DIRECTORY,
    embedding_function=embeddings
)

# Questions to check
questions = [
    "Does CloudFuze maintain 'created by' metadata when migrating SharePoint to OneDrive?",
    "How does JSON work in Slack to Teams migration?",
    "How does CloudFuze handle permission mapping when migrating shared folders from Google Drive to Microsoft 365 OneDrive, especially when the original sharing structure includes external collaborators and nested folder level permissions?",
    "Does CloudFuze migrate Groups from Box to MS?",
    "what metadata is migrated from dropbox to google?",
    "how many messages can we migrate per day from slack to teams?"
]

def check_question(question: str, k: int = 5):
    """Check if we have relevant content for a question."""
    print(f"\n{'='*70}")
    print(f"QUESTION: {question}")
    print(f"{'='*70}\n")
    
    # Search vectorstore
    results = vectorstore.similarity_search_with_score(question, k=k)
    
    if not results:
        print("❌ NO CONTENT FOUND")
        return False
    
    print(f"✅ FOUND {len(results)} RELEVANT DOCUMENTS:\n")
    
    for idx, (doc, score) in enumerate(results, 1):
        source_type = doc.metadata.get('source_type', 'unknown')
        source = doc.metadata.get('source', 'unknown')
        
        # Calculate similarity percentage (distance to similarity)
        similarity = 1 - score
        similarity_pct = similarity * 100
        
        print(f"  [{idx}] Source: {source_type.upper()} | Similarity: {similarity_pct:.1f}%")
        
        # Show specific metadata based on source type
        if source_type == "blog":
            title = doc.metadata.get('title', 'Untitled')
            print(f"      Title: {title}")
        elif source_type == "outlook":
            subject = doc.metadata.get('conversation_topic', 'No Subject')
            participants = doc.metadata.get('participants', 'Unknown')
            print(f"      Subject: {subject}")
            print(f"      Participants: {participants[:80]}...")
        elif source_type == "sharepoint":
            filename = doc.metadata.get('filename', 'Unknown')
            path = doc.metadata.get('file_path', '')
            print(f"      File: {filename}")
            if path:
                print(f"      Path: {path[:80]}...")
        
        # Show content preview
        content_preview = doc.page_content[:200].replace('\n', ' ')
        print(f"      Preview: {content_preview}...\n")
    
    return True

# Check each question
print(f"Checking {len(questions)} questions...\n")

results_summary = []
for question in questions:
    has_content = check_question(question, k=5)
    results_summary.append((question, has_content))

# Summary
print("\n" + "="*70)
print("  SUMMARY")
print("="*70 + "\n")

for question, has_content in results_summary:
    status = "✅ HAS CONTENT" if has_content else "❌ NO CONTENT"
    print(f"{status}: {question[:60]}...")

print(f"\n{'='*70}\n")

# Count by content availability
has_content_count = sum(1 for _, has_content in results_summary if has_content)
print(f"Questions with content: {has_content_count}/{len(questions)}")
print(f"Questions without content: {len(questions) - has_content_count}/{len(questions)}")

if has_content_count == len(questions):
    print("\n🎉 ALL QUESTIONS HAVE RELEVANT CONTENT IN VECTORSTORE!")
elif has_content_count >= len(questions) * 0.8:
    print("\n✅ MOST QUESTIONS HAVE RELEVANT CONTENT!")
else:
    print("\n⚠️ MANY QUESTIONS LACK RELEVANT CONTENT!")

print()

