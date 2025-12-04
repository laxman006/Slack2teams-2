"""
Analyze User Questions from MongoDB Chat History

This script:
1. Extracts all user questions from chat history
2. Finds most popular/frequent questions
3. Filters by relevance to knowledge base
4. Updates suggested_questions collection

Usage:
    python -m scripts.analyze_user_questions
"""

import sys
import os
from datetime import datetime, timedelta
from collections import Counter
import re
from typing import List, Dict, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from config import MONGODB_URL, MONGODB_DATABASE


def clean_question(text: str) -> str:
    """Clean and normalize question text"""
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep question marks
    text = re.sub(r'[^\w\s?.,!-]', '', text)
    
    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]
    
    # Ensure it ends with a question mark if it looks like a question
    question_starters = ['how', 'what', 'when', 'where', 'why', 'who', 'can', 'is', 'does', 'do', 'will', 'should']
    first_word = text.lower().split()[0] if text else ''
    
    if first_word in question_starters and not text.endswith('?'):
        text += '?'
    
    return text.strip()


def is_valid_question(text: str) -> bool:
    """Check if text is a valid question"""
    if not text or len(text) < 10:
        return False
    
    # Must be reasonable length
    if len(text) > 200:
        return False
    
    # Must have question-like patterns
    question_patterns = [
        r'^(how|what|when|where|why|who|can|is|does|do|will|should|could|would)\s',
        r'\?$'
    ]
    
    for pattern in question_patterns:
        if re.search(pattern, text.lower()):
            return True
    
    return False


def calculate_similarity_score(q1: str, q2: str) -> float:
    """Calculate simple similarity between two questions"""
    words1 = set(q1.lower().split())
    words2 = set(q2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)


def deduplicate_questions(questions: List[Tuple[str, int]], threshold: float = 0.7) -> List[Tuple[str, int]]:
    """Remove duplicate or very similar questions"""
    unique_questions = []
    
    for question, count in questions:
        is_duplicate = False
        
        for existing_q, existing_count in unique_questions:
            similarity = calculate_similarity_score(question, existing_q)
            
            if similarity > threshold:
                # Merge counts if very similar
                is_duplicate = True
                # Keep the more popular one
                if count > existing_count:
                    unique_questions.remove((existing_q, existing_count))
                    unique_questions.append((question, count + existing_count))
                else:
                    # Add count to existing
                    unique_questions.remove((existing_q, existing_count))
                    unique_questions.append((existing_q, count + existing_count))
                break
        
        if not is_duplicate:
            unique_questions.append((question, count))
    
    return sorted(unique_questions, key=lambda x: x[1], reverse=True)


def categorize_question(question: str) -> str:
    """Categorize question based on content"""
    question_lower = question.lower()
    
    # Migration keywords
    if any(word in question_lower for word in ['migrate', 'migration', 'transfer', 'move', 'sync']):
        return 'migration'
    
    # Security keywords
    if any(word in question_lower for word in ['security', 'secure', 'encryption', 'safe', 'privacy', 'protect']):
        return 'security'
    
    # Pricing keywords
    if any(word in question_lower for word in ['price', 'pricing', 'cost', 'pay', 'plan', 'trial', 'free']):
        return 'pricing'
    
    # Features keywords
    if any(word in question_lower for word in ['feature', 'capability', 'function', 'support', 'option', 'can i', 'does it']):
        return 'features'
    
    # Support keywords
    if any(word in question_lower for word in ['help', 'support', 'problem', 'issue', 'error', 'fail', 'how to']):
        return 'support'
    
    # Integration keywords
    if any(word in question_lower for word in ['platform', 'integration', 'compatible', 'work with']):
        return 'integration'
    
    return 'general'


def extract_keywords(question: str) -> List[str]:
    """Extract important keywords from question"""
    # Common words to ignore
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'could', 'may', 'might', 'must', 'can', 'i', 'you', 'we', 'they',
        'me', 'him', 'her', 'it', 'us', 'them', 'my', 'your', 'his', 'its',
        'our', 'their', 'this', 'that', 'these', 'those', 'to', 'from', 'in',
        'on', 'at', 'by', 'for', 'with', 'about', 'as', 'of', 'or', 'and'
    }
    
    # Extract words
    words = re.findall(r'\b[a-z]+\b', question.lower())
    
    # Filter and return
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords[:10]  # Limit to top 10 keywords


def analyze_user_questions(days_back: int = 30, min_frequency: int = 2, limit: int = 20):
    """
    Analyze user questions from chat history and update suggested questions
    
    Args:
        days_back: How many days of history to analyze
        min_frequency: Minimum times a question must be asked to be included
        limit: Maximum number of questions to add/update
    """
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URL)
        db = client[MONGODB_DATABASE]
        chat_collection = db.chat_histories  # Note: plural
        suggested_collection = db.suggested_questions
        
        print("\n" + "="*70)
        print("   ANALYZE USER QUESTIONS FROM CHAT HISTORY")
        print("="*70 + "\n")
        
        # Calculate date threshold
        date_threshold = datetime.utcnow() - timedelta(days=days_back)
        print(f"📅 Analyzing questions from last {days_back} days")
        print(f"   (Since: {date_threshold.strftime('%Y-%m-%d %H:%M:%S')})\n")
        
        # Fetch all user chat histories
        print("📊 Fetching chat histories from MongoDB...")
        
        # Query all documents with messages
        chat_docs = chat_collection.find(
            {"messages": {"$exists": True, "$ne": []}},
            {"user_id": 1, "messages": 1, "last_updated": 1}
        )
        
        # Extract user questions
        all_questions = []
        user_count = 0
        message_count = 0
        
        for doc in chat_docs:
            user_count += 1
            messages = doc.get('messages', [])
            
            for msg in messages:
                message_count += 1
                
                # Skip if too old
                msg_timestamp = msg.get('timestamp')
                if msg_timestamp and isinstance(msg_timestamp, datetime):
                    if msg_timestamp < date_threshold:
                        continue
                
                # Only process user messages
                if msg.get('role') == 'user':
                    content = msg.get('content', '').strip()
                    
                    if is_valid_question(content):
                        cleaned = clean_question(content)
                        if cleaned:
                            all_questions.append(cleaned)
        
        print(f"✅ Processed {user_count} users, {message_count} messages")
        print(f"✅ Found {len(all_questions)} valid user questions\n")
        
        if not all_questions:
            print("⚠️  No questions found in chat history!")
            print("   Make sure users have asked questions in the chat.\n")
            client.close()
            return
        
        # Count question frequency
        print("📈 Analyzing question frequency...")
        question_counter = Counter(all_questions)
        
        # Get most common questions
        popular_questions = [
            (q, count) for q, count in question_counter.most_common()
            if count >= min_frequency
        ]
        
        print(f"✅ Found {len(popular_questions)} questions asked {min_frequency}+ times\n")
        
        if not popular_questions:
            print(f"⚠️  No questions found with minimum frequency of {min_frequency}")
            print(f"   Highest frequency: {question_counter.most_common(1)[0][1] if question_counter else 0}\n")
            client.close()
            return
        
        # Deduplicate similar questions
        print("🔍 Removing duplicate and similar questions...")
        unique_questions = deduplicate_questions(popular_questions)
        print(f"✅ After deduplication: {len(unique_questions)} unique questions\n")
        
        # Take top N questions
        top_questions = unique_questions[:limit]
        
        # Categorize and prepare for database
        print("📂 Categorizing and preparing questions...\n")
        print("-"*70)
        
        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        for question, frequency in top_questions:
            # Check if question already exists
            existing = suggested_collection.find_one({"question_text": question})
            
            if existing:
                # Update priority based on frequency
                new_priority = min(95, 50 + (frequency * 5))  # Cap at 95
                
                suggested_collection.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$set": {
                            "priority": new_priority,
                            "updated_at": datetime.utcnow(),
                            "user_asked_count": frequency
                        }
                    }
                )
                
                print(f"🔄 Updated: {question[:60]}...")
                print(f"   Frequency: {frequency}, Priority: {new_priority}\n")
                updated_count += 1
            else:
                # Add new question
                category = categorize_question(question)
                keywords = extract_keywords(question)
                priority = min(95, 50 + (frequency * 5))  # Cap at 95
                
                question_doc = {
                    "question_text": question,
                    "category": category,
                    "priority": priority,
                    "keywords": keywords,
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "display_count": 0,
                    "click_count": 0,
                    "click_rate": 0.0,
                    "user_asked_count": frequency,
                    "source": "user_history",
                    "created_by": "auto_analyzer"
                }
                
                suggested_collection.insert_one(question_doc)
                
                print(f"✅ Added: {question}")
                print(f"   Category: {category}, Frequency: {frequency}, Priority: {priority}")
                print(f"   Keywords: {', '.join(keywords[:5])}\n")
                added_count += 1
        
        print("-"*70)
        print("\n" + "="*70)
        print("🎉 Analysis Complete!")
        print("="*70)
        print(f"   ✅ Added: {added_count} new questions")
        print(f"   🔄 Updated: {updated_count} existing questions")
        print(f"   📊 Total in DB: {suggested_collection.count_documents({})}")
        print("="*70 + "\n")
        
        # Show top 10 most popular
        print("🔥 Top 10 Most Popular Questions:\n")
        for i, (question, freq) in enumerate(top_questions[:10], 1):
            print(f"{i:2d}. [{freq:2d}x] {question}")
        
        print("\n" + "="*70 + "\n")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error analyzing questions: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze user questions from chat history')
    parser.add_argument('--days', type=int, default=30, help='Days of history to analyze (default: 30)')
    parser.add_argument('--min-freq', type=int, default=2, help='Minimum frequency (default: 2)')
    parser.add_argument('--limit', type=int, default=20, help='Maximum questions to add (default: 20)')
    
    args = parser.parse_args()
    
    analyze_user_questions(
        days_back=args.days,
        min_frequency=args.min_freq,
        limit=args.limit
    )

