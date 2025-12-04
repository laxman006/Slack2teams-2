"""
Reset Suggested Questions - Clear old and seed new questions

This script removes all existing questions and reseeds with the improved set.

Usage:
    python -m scripts.reset_questions
"""

import sys
import os
from pymongo import MongoClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MONGODB_URL, MONGODB_DATABASE

def reset_questions():
    """Clear all existing questions and reseed"""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URL)
        db = client[MONGODB_DATABASE]
        collection = db.suggested_questions
        
        print("\n" + "="*60)
        print("   RESET SUGGESTED QUESTIONS")
        print("="*60 + "\n")
        
        # Count existing questions
        existing_count = collection.count_documents({})
        print(f"📊 Current questions in database: {existing_count}")
        
        if existing_count > 0:
            # Delete all existing questions
            result = collection.delete_many({})
            print(f"🗑️  Deleted {result.deleted_count} old questions")
        else:
            print("ℹ️  No existing questions to delete")
        
        print("\n" + "-"*60)
        print("Now run: python -m scripts.seed_suggested_questions")
        print("-"*60 + "\n")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error resetting questions: {e}")
        sys.exit(1)


if __name__ == "__main__":
    reset_questions()

