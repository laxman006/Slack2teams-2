#!/usr/bin/env python3
"""
Test script to verify MongoDB integration is working correctly.
This script tests the basic MongoDB operations without affecting existing data.
"""

import asyncio
from datetime import datetime
from app.mongodb_memory import mongodb_memory

async def test_mongodb_connection():
    """Test MongoDB connection and basic operations."""
    
    print("Testing MongoDB Integration")
    print("=" * 30)
    
    try:
        # Test connection
        print("1. Testing MongoDB connection...")
        await mongodb_memory.connect()
        print("✅ Connected to MongoDB successfully")
        
        # Test creating a test user conversation
        print("\n2. Testing conversation creation...")
        test_user_id = "test_migration_user_12345"
        
        # Get or create conversation
        conversation = await mongodb_memory.get_or_create_user_conversation(test_user_id)
        print(f"✅ Retrieved/created conversation for user: {test_user_id}")
        print(f"   Initial message count: {len(conversation)}")
        
        # Test adding messages
        print("\n3. Testing message addition...")
        await mongodb_memory.add_to_conversation(test_user_id, "user", "Hello, this is a test message!")
        await mongodb_memory.add_to_conversation(test_user_id, "assistant", "Hello! This is a test response from the assistant.")
        
        # Verify messages were added
        updated_conversation = await mongodb_memory.get_or_create_user_conversation(test_user_id)
        print(f"✅ Added messages successfully")
        print(f"   Updated message count: {len(updated_conversation)}")
        
        # Test conversation context
        print("\n4. Testing conversation context...")
        context = await mongodb_memory.get_conversation_context(test_user_id)
        print("✅ Retrieved conversation context:")
        print(f"   Context length: {len(context)} characters")
        
        # Test getting full chat history
        print("\n5. Testing full chat history retrieval...")
        full_history = await mongodb_memory.get_user_chat_history(test_user_id)
        print(f"✅ Retrieved full chat history: {len(full_history)} messages")
        
        # Test conversation stats
        print("\n6. Testing conversation statistics...")
        stats = await mongodb_memory.get_conversation_stats()
        print("✅ Retrieved conversation statistics:")
        print(f"   Total users: {stats.get('total_users', 0)}")
        print(f"   Total messages: {stats.get('total_messages', 0)}")
        
        # Test clearing chat history
        print("\n7. Testing chat history clearing...")
        await mongodb_memory.clear_user_chat_history(test_user_id)
        cleared_conversation = await mongodb_memory.get_or_create_user_conversation(test_user_id)
        print(f"✅ Cleared chat history successfully")
        print(f"   Message count after clearing: {len(cleared_conversation)}")
        
        print("\n" + "=" * 50)
        print("🎉 All MongoDB integration tests passed!")
        print("Your MongoDB setup is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Please check your MongoDB configuration and ensure MongoDB is running.")
        return False
    
    finally:
        # Clean up test data
        try:
            await mongodb_memory.clear_user_chat_history("test_migration_user_12345")
            print("\n🧹 Cleaned up test data")
        except:
            pass
        
        # Close connection
        await mongodb_memory.disconnect()
        print("Disconnected from MongoDB")

async def main():
    """Main test function."""
    success = await test_mongodb_connection()
    
    if success:
        print("\n✅ MongoDB integration is ready!")
        print("You can now run the migration script to transfer your JSON data.")
    else:
        print("\n❌ MongoDB integration test failed.")
        print("Please fix the issues before proceeding with migration.")

if __name__ == "__main__":
    asyncio.run(main())
