"""
Seed Script for Suggested Questions

This script populates the database with initial suggested questions.
Run this once after setting up the dynamic questions system.

Usage:
    python -m scripts.seed_suggested_questions
"""

import sys
import os
from datetime import datetime
from pymongo import MongoClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MONGODB_URL, MONGODB_DATABASE

# Initial questions to seed - IMPROVED VERSION
INITIAL_QUESTIONS = [
    # Top Priority - Most Common Questions (90-95)
    {
        "question_text": "How do I migrate from Google Drive to OneDrive?",
        "category": "migration",
        "priority": 95,
        "keywords": ["google drive", "onedrive", "microsoft", "migration", "files"],
        "status": "active"
    },
    {
        "question_text": "Can I migrate Slack channels to Microsoft Teams?",
        "category": "migration",
        "priority": 92,
        "keywords": ["slack", "teams", "microsoft", "channels", "chat", "migration"],
        "status": "active"
    },
    {
        "question_text": "How secure is my data during migration?",
        "category": "security",
        "priority": 90,
        "keywords": ["security", "encryption", "safe", "data protection", "privacy"],
        "status": "active"
    },
    {
        "question_text": "What's the fastest way to migrate SharePoint Online?",
        "category": "migration",
        "priority": 88,
        "keywords": ["sharepoint", "migration", "fast", "quick", "speed"],
        "status": "active"
    },
    
    # High Priority - Important Use Cases (80-89)
    {
        "question_text": "Can I migrate from Box to Google Drive?",
        "category": "migration",
        "priority": 85,
        "keywords": ["box", "google drive", "migration", "cloud storage"],
        "status": "active"
    },
    {
        "question_text": "How do I preserve permissions during migration?",
        "category": "features",
        "priority": 83,
        "keywords": ["permissions", "access control", "security", "preserve", "migration"],
        "status": "active"
    },
    {
        "question_text": "Can I schedule migrations to run automatically?",
        "category": "features",
        "priority": 80,
        "keywords": ["scheduled", "automation", "automatic", "recurring", "migrations"],
        "status": "active"
    },
    {
        "question_text": "How do I track my migration progress?",
        "category": "features",
        "priority": 80,
        "keywords": ["progress", "tracking", "monitor", "status", "dashboard"],
        "status": "active"
    },
    
    # Medium-High Priority - Feature Questions (70-79)
    {
        "question_text": "Which cloud platforms does CloudFuze support?",
        "category": "integration",
        "priority": 78,
        "keywords": ["platforms", "support", "integrations", "compatible", "services"],
        "status": "active"
    },
    {
        "question_text": "Can I migrate large files over 5GB?",
        "category": "features",
        "priority": 75,
        "keywords": ["large files", "size limit", "5gb", "big files", "migration"],
        "status": "active"
    },
    {
        "question_text": "How long does a typical migration take?",
        "category": "general",
        "priority": 73,
        "keywords": ["duration", "time", "speed", "how long", "migration"],
        "status": "active"
    },
    {
        "question_text": "Can I do a trial migration before the full migration?",
        "category": "features",
        "priority": 70,
        "keywords": ["trial", "test", "demo", "preview", "dry run"],
        "status": "active"
    },
    
    # Medium Priority - Getting Started (65-69)
    {
        "question_text": "What's included in the free trial?",
        "category": "pricing",
        "priority": 68,
        "keywords": ["free trial", "demo", "pricing", "cost", "test"],
        "status": "active"
    },
    {
        "question_text": "How do I get started with my first migration?",
        "category": "support",
        "priority": 65,
        "keywords": ["getting started", "first", "setup", "begin", "start"],
        "status": "active"
    },
    
    # Strategic Questions - Business Value (75-85)
    {
        "question_text": "What happens if my migration fails?",
        "category": "support",
        "priority": 82,
        "keywords": ["fail", "error", "problem", "rollback", "support"],
        "status": "active"
    },
    {
        "question_text": "Can I migrate incremental changes after initial migration?",
        "category": "features",
        "priority": 77,
        "keywords": ["incremental", "delta", "sync", "changes", "updates"],
        "status": "active"
    },
    {
        "question_text": "Does CloudFuze support Office 365 tenant-to-tenant migration?",
        "category": "migration",
        "priority": 86,
        "keywords": ["office 365", "tenant", "microsoft", "o365", "migration"],
        "status": "active"
    },
    {
        "question_text": "Can I migrate Gmail to Office 365?",
        "category": "migration",
        "priority": 84,
        "keywords": ["gmail", "office 365", "email", "google", "microsoft"],
        "status": "active"
    },
    
    # Specific Platform Questions (70-85)
    {
        "question_text": "How do I migrate from Dropbox Business to SharePoint?",
        "category": "migration",
        "priority": 81,
        "keywords": ["dropbox", "sharepoint", "business", "migration"],
        "status": "active"
    },
    {
        "question_text": "Can CloudFuze migrate Google Workspace to Microsoft 365?",
        "category": "migration",
        "priority": 87,
        "keywords": ["google workspace", "microsoft 365", "gsuite", "m365", "migration"],
        "status": "active"
    },
    
    # Technical Questions (65-75)
    {
        "question_text": "Will metadata and timestamps be preserved?",
        "category": "features",
        "priority": 72,
        "keywords": ["metadata", "timestamps", "dates", "preserve", "migration"],
        "status": "active"
    },
    {
        "question_text": "Can I filter which files to migrate?",
        "category": "features",
        "priority": 68,
        "keywords": ["filter", "selective", "choose", "exclude", "migration"],
        "status": "active"
    },
    
    # Business & Pricing (60-70)
    {
        "question_text": "How is CloudFuze pricing calculated?",
        "category": "pricing",
        "priority": 66,
        "keywords": ["pricing", "cost", "calculate", "billing", "plans"],
        "status": "active"
    },
    {
        "question_text": "Is there dedicated support during migration?",
        "category": "support",
        "priority": 64,
        "keywords": ["support", "help", "dedicated", "assistance", "migration"],
        "status": "active"
    }
]


def seed_questions():
    """Seed the database with initial suggested questions"""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URL)
        db = client[MONGODB_DATABASE]
        collection = db.suggested_questions
        
        print("🌱 Starting to seed suggested questions...")
        print(f"📊 Total questions to seed: {len(INITIAL_QUESTIONS)}")
        
        # Check if questions already exist
        existing_count = collection.count_documents({})
        if existing_count > 0:
            print(f"\n⚠️  Found {existing_count} existing questions in the database")
            response = input("Do you want to proceed? This will add more questions (y/n): ")
            if response.lower() != 'y':
                print("❌ Seeding cancelled")
                return
        
        # Prepare questions with timestamps
        seeded_count = 0
        skipped_count = 0
        
        for q_data in INITIAL_QUESTIONS:
            # Check if question already exists
            existing = collection.find_one({"question_text": q_data["question_text"]})
            if existing:
                print(f"⏩ Skipped (already exists): {q_data['question_text'][:60]}...")
                skipped_count += 1
                continue
            
            # Add metadata
            question_doc = {
                **q_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "display_count": 0,
                "click_count": 0,
                "click_rate": 0.0,
                "target_user_roles": [],
                "created_by": "system_seed"
            }
            
            # Insert into database
            result = collection.insert_one(question_doc)
            print(f"✅ Added: {q_data['question_text']}")
            seeded_count += 1
        
        # Summary
        print(f"\n{'='*60}")
        print(f"🎉 Seeding completed successfully!")
        print(f"   ✅ Added: {seeded_count} questions")
        print(f"   ⏩ Skipped: {skipped_count} questions (already existed)")
        print(f"   📊 Total in DB: {collection.count_documents({})}")
        print(f"{'='*60}\n")
        
        # Show breakdown by category
        print("📂 Questions by category:")
        for category in ["migration", "features", "pricing", "integration", "security", "support", "general"]:
            count = collection.count_documents({"category": category})
            print(f"   - {category.capitalize()}: {count}")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error seeding questions: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("   SUGGESTED QUESTIONS SEED SCRIPT")
    print("="*60 + "\n")
    seed_questions()

