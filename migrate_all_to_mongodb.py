#!/usr/bin/env python3
"""
Migrate ALL remaining local data to MongoDB Atlas.

This script will migrate:
1. Fine-tuning dataset (corrections, training data)
2. Fine-tuning status
3. Feedback history
4. Corrected responses
5. Bad responses traces
6. Vectorstore metadata
7. Chat history (if not already migrated)
"""

import os
import json
from datetime import datetime
from pymongo import MongoClient
from config import MONGODB_URL, MONGODB_DATABASE

def migrate_all_data():
    """Migrate all local data files to MongoDB."""
    
    print("=" * 70)
    print("MIGRATE ALL DATA TO MONGODB ATLAS")
    print("=" * 70)
    
    # Connect to MongoDB
    print(f"\n[*] Connecting to MongoDB Atlas...")
    try:
        client = MongoClient(MONGODB_URL)
        db = client[MONGODB_DATABASE]
        print(f"[OK] Connected to database: {MONGODB_DATABASE}")
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        return False
    
    migrated_count = 0
    total_items = 0
    
    # 1. Migrate Fine-Tuning Dataset
    print("\n" + "-" * 70)
    print("1. FINE-TUNING DATASET")
    print("-" * 70)
    
    finetuning_collection = db["fine_tuning_data"]
    
    # Migrate corrections.jsonl
    corrections_file = "./data/fine_tuning_dataset/corrections.jsonl"
    if os.path.exists(corrections_file):
        print(f"[*] Migrating {corrections_file}...")
        corrections = []
        with open(corrections_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    corrections.append(json.loads(line))
        
        if corrections:
            # Clear existing and insert
            finetuning_collection.delete_many({"type": "correction"})
            for correction in corrections:
                correction["type"] = "correction"
                correction["migrated_at"] = datetime.utcnow()
            finetuning_collection.insert_many(corrections)
            print(f"[OK] Migrated {len(corrections)} corrections")
            migrated_count += len(corrections)
            total_items += len(corrections)
    
    # Migrate training data files
    training_files = [f for f in os.listdir("./data/fine_tuning_dataset/") 
                     if f.startswith("training_data_") and f.endswith(".jsonl")]
    
    for training_file in training_files:
        file_path = f"./data/fine_tuning_dataset/{training_file}"
        print(f"[*] Migrating {training_file}...")
        training_data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    training_data.append(json.loads(line))
        
        if training_data:
            for item in training_data:
                item["type"] = "training_data"
                item["source_file"] = training_file
                item["migrated_at"] = datetime.utcnow()
            finetuning_collection.insert_many(training_data)
            print(f"[OK] Migrated {len(training_data)} training examples")
            migrated_count += len(training_data)
            total_items += len(training_data)
    
    # 2. Migrate Fine-Tuning Status
    print("\n" + "-" * 70)
    print("2. FINE-TUNING STATUS")
    print("-" * 70)
    
    status_file = "./data/fine_tuning_status.json"
    if os.path.exists(status_file):
        print(f"[*] Migrating {status_file}...")
        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)
        
        status_data["migrated_at"] = datetime.utcnow()
        db["fine_tuning_status"].replace_one(
            {"job_id": status_data.get("job_id", "current")},
            status_data,
            upsert=True
        )
        print(f"[OK] Migrated fine-tuning status")
        migrated_count += 1
        total_items += 1
    
    # 3. Migrate Feedback History
    print("\n" + "-" * 70)
    print("3. FEEDBACK HISTORY")
    print("-" * 70)
    
    feedback_file = "./data/feedback_history.json"
    if os.path.exists(feedback_file):
        print(f"[*] Migrating {feedback_file}...")
        with open(feedback_file, 'r', encoding='utf-8') as f:
            feedback_data = json.load(f)
        
        feedback_collection = db["feedback_history"]
        feedback_collection.delete_many({})  # Clear existing
        
        feedback_items = []
        for user_id, feedbacks in feedback_data.items():
            if isinstance(feedbacks, list):
                for feedback in feedbacks:
                    if isinstance(feedback, dict):
                        feedback["user_id"] = user_id
                        feedback["migrated_at"] = datetime.utcnow()
                        feedback_items.append(feedback)
            elif isinstance(feedbacks, dict):
                # Single feedback item
                feedbacks["user_id"] = user_id
                feedbacks["migrated_at"] = datetime.utcnow()
                feedback_items.append(feedbacks)
            else:
                # String or other type, wrap it
                feedback_items.append({
                    "user_id": user_id,
                    "data": feedbacks,
                    "migrated_at": datetime.utcnow()
                })
        
        if feedback_items:
            feedback_collection.insert_many(feedback_items)
            print(f"[OK] Migrated {len(feedback_items)} feedback items")
            migrated_count += len(feedback_items)
            total_items += len(feedback_items)
    
    # 4. Migrate Corrected Responses
    print("\n" + "-" * 70)
    print("4. CORRECTED RESPONSES")
    print("-" * 70)
    
    corrected_file = "./data/corrected_responses/corrected_responses.json"
    if os.path.exists(corrected_file):
        print(f"[*] Migrating {corrected_file}...")
        with open(corrected_file, 'r', encoding='utf-8') as f:
            corrected_data = json.load(f)
        
        corrected_collection = db["corrected_responses"]
        corrected_collection.delete_many({})  # Clear existing
        
        corrected_items = []
        for key, value in corrected_data.items():
            item = value if isinstance(value, dict) else {"data": value}
            item["key"] = key
            item["migrated_at"] = datetime.utcnow()
            corrected_items.append(item)
        
        if corrected_items:
            corrected_collection.insert_many(corrected_items)
            print(f"[OK] Migrated {len(corrected_items)} corrected responses")
            migrated_count += len(corrected_items)
            total_items += len(corrected_items)
    
    # 5. Migrate Bad Responses
    print("\n" + "-" * 70)
    print("5. BAD RESPONSES TRACES")
    print("-" * 70)
    
    bad_responses_file = "./data/bad_responses.jsonl"
    if os.path.exists(bad_responses_file):
        print(f"[*] Migrating {bad_responses_file}...")
        bad_responses = []
        with open(bad_responses_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    bad_responses.append(json.loads(line))
        
        if bad_responses:
            bad_collection = db["bad_responses"]
            bad_collection.delete_many({})  # Clear existing
            for response in bad_responses:
                response["migrated_at"] = datetime.utcnow()
            bad_collection.insert_many(bad_responses)
            print(f"[OK] Migrated {len(bad_responses)} bad response traces")
            migrated_count += len(bad_responses)
            total_items += len(bad_responses)
    
    # 6. Migrate Vectorstore Metadata
    print("\n" + "-" * 70)
    print("6. VECTORSTORE METADATA")
    print("-" * 70)
    
    metadata_file = "./data/vectorstore_metadata.json"
    if os.path.exists(metadata_file):
        print(f"[*] Migrating {metadata_file}...")
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        metadata["migrated_at"] = datetime.utcnow()
        db["vectorstore_metadata"].replace_one(
            {"_id": "current"},
            {**metadata, "_id": "current"},
            upsert=True
        )
        print(f"[OK] Migrated vectorstore metadata")
        migrated_count += 1
        total_items += 1
    
    # 7. Check if Chat History needs migration
    print("\n" + "-" * 70)
    print("7. CHAT HISTORY")
    print("-" * 70)
    
    chat_collection = db["chat_histories"]
    existing_chats = chat_collection.count_documents({})
    
    if existing_chats > 0:
        print(f"[OK] Chat history already in MongoDB ({existing_chats} conversations)")
    else:
        print("[*] Chat history can be migrated using migrate_to_mongodb.py")
    
    # Summary
    print("\n" + "=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    print(f"Total items migrated: {migrated_count}")
    print(f"Total documents in MongoDB: {total_items}")
    
    # Show final collections
    print("\n[*] MongoDB Collections after migration:")
    for collection_name in db.list_collection_names():
        count = db[collection_name].count_documents({})
        print(f"   ✅ {collection_name}: {count} documents")
    
    client.close()
    
    print("\n✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("\nNext steps:")
    print("  1. Update application to read from MongoDB")
    print("  2. Test that everything works")
    print("  3. Backup and remove local files")
    
    return True


if __name__ == "__main__":
    print("\nMigrate All Data to MongoDB Atlas")
    print("=" * 70)
    print("\nThis will migrate ALL your local data files to MongoDB:")
    print("  • Fine-tuning dataset")
    print("  • Fine-tuning status")
    print("  • Feedback history")
    print("  • Corrected responses")
    print("  • Bad responses traces")
    print("  • Vectorstore metadata")
    print("\nYour local files will NOT be deleted (you can remove them later).")
    
    confirm = input("\nContinue with migration? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        success = migrate_all_data()
        if success:
            print("\n🎉 All data is now in MongoDB Atlas!")
            print("\nSee MONGODB-DATA-ACCESS.md for how to use the migrated data.")
        else:
            print("\n❌ Migration failed. Check the errors above.")
    else:
        print("\n[*] Migration cancelled")

