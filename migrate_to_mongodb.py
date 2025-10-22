#!/usr/bin/env python3
"""
Migration script to transfer chat history from JSON file to MongoDB.
This script will read the existing chat_history.json file and migrate all data to MongoDB.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

from app.mongodb_memory import mongodb_memory
from config import JSON_MEMORY_FILE, MONGODB_DATABASE, MONGODB_CHAT_COLLECTION

async def migrate_chat_history():
    """Migrate chat history from JSON file to MongoDB."""
    
    print("Starting migration from JSON to MongoDB...")
    print(f"Source file: {JSON_MEMORY_FILE}")
    print(f"Target database: {MONGODB_DATABASE}.{MONGODB_CHAT_COLLECTION}")
    
    # Connect to MongoDB
    try:
        await mongodb_memory.connect()
        print("✅ Connected to MongoDB successfully")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False
    
    # Load JSON data
    if not os.path.exists(JSON_MEMORY_FILE):
        print(f"❌ JSON file not found: {JSON_MEMORY_FILE}")
        return False
    
    try:
        with open(JSON_MEMORY_FILE, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        print(f"✅ Loaded JSON data with {len(json_data)} users")
    except Exception as e:
        print(f"❌ Failed to load JSON file: {e}")
        return False
    
    # Migrate each user's data
    migrated_count = 0
    failed_count = 0
    
    for user_id, user_data in json_data.items():
        try:
            # Convert timestamps to datetime objects if they're strings
            messages = user_data.get("messages", [])
            for message in messages:
                if isinstance(message.get("timestamp"), str):
                    try:
                        message["timestamp"] = datetime.fromisoformat(message["timestamp"].replace('Z', '+00:00'))
                    except ValueError:
                        # If parsing fails, keep as string
                        pass
            
            # Convert created_at and last_updated to datetime if they're strings
            if isinstance(user_data.get("created_at"), str):
                try:
                    user_data["created_at"] = datetime.fromisoformat(user_data["created_at"].replace('Z', '+00:00'))
                except ValueError:
                    user_data["created_at"] = datetime.utcnow()
            
            if isinstance(user_data.get("last_updated"), str):
                try:
                    user_data["last_updated"] = datetime.fromisoformat(user_data["last_updated"].replace('Z', '+00:00'))
                except ValueError:
                    user_data["last_updated"] = datetime.utcnow()
            
            # Prepare document for MongoDB
            mongo_doc = {
                "user_id": user_id,
                "messages": messages,
                "created_at": user_data.get("created_at", datetime.utcnow()),
                "last_updated": user_data.get("last_updated", datetime.utcnow())
            }
            
            # Insert or update in MongoDB
            await mongodb_memory.collection.replace_one(
                {"user_id": user_id},
                mongo_doc,
                upsert=True
            )
            
            migrated_count += 1
            print(f"✅ Migrated user: {user_id} ({len(messages)} messages)")
            
        except Exception as e:
            failed_count += 1
            print(f"❌ Failed to migrate user {user_id}: {e}")
    
    # Print summary
    print("\n" + "="*50)
    print("MIGRATION SUMMARY")
    print("="*50)
    print(f"Total users in JSON: {len(json_data)}")
    print(f"Successfully migrated: {migrated_count}")
    print(f"Failed migrations: {failed_count}")
    
    if failed_count == 0:
        print("🎉 Migration completed successfully!")
        
        # Verify migration
        try:
            stats = await mongodb_memory.get_conversation_stats()
            print(f"\nMongoDB Stats:")
            print(f"  Total users: {stats.get('total_users', 0)}")
            print(f"  Total messages: {stats.get('total_messages', 0)}")
        except Exception as e:
            print(f"Warning: Could not verify migration stats: {e}")
        
        return True
    else:
        print(f"⚠️  Migration completed with {failed_count} failures")
        return False

async def main():
    """Main migration function."""
    print("Chat History Migration Tool")
    print("=" * 30)
    
    # Check if JSON file exists
    if not os.path.exists(JSON_MEMORY_FILE):
        print(f"❌ JSON file not found: {JSON_MEMORY_FILE}")
        print("Make sure the file exists before running migration.")
        return
    
    # Confirm migration
    print(f"This will migrate data from {JSON_MEMORY_FILE} to MongoDB.")
    print("The original JSON file will NOT be modified.")
    
    try:
        # Run migration
        success = await migrate_chat_history()
        
        if success:
            print("\n✅ Migration completed successfully!")
            print("You can now start using MongoDB for chat history storage.")
        else:
            print("\n❌ Migration completed with errors.")
            print("Please check the error messages above.")
    
    except KeyboardInterrupt:
        print("\n⚠️  Migration cancelled by user")
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
    finally:
        # Close MongoDB connection
        await mongodb_memory.disconnect()
        print("Disconnected from MongoDB")

if __name__ == "__main__":
    asyncio.run(main())
