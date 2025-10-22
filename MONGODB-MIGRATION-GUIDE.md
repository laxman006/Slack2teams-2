# MongoDB Migration Guide

This guide will help you migrate your chat history from JSON file storage to MongoDB.

## Overview

Your application has been updated to use MongoDB for chat history storage instead of JSON files. This provides better scalability, performance, and data management capabilities.

## What Changed

1. **Configuration**: Added MongoDB settings to `config.py`
2. **Endpoints**: Updated `app/endpoints.py` to use MongoDB memory manager
3. **Dependencies**: Added MongoDB drivers to `requirements.txt`
4. **Migration Tools**: Created scripts to migrate existing data

## Prerequisites

### 1. Install MongoDB

**Option A: Local MongoDB Installation**
```bash
# Windows (using Chocolatey)
choco install mongodb

# macOS (using Homebrew)
brew install mongodb-community

# Ubuntu/Debian
sudo apt-get install mongodb

# Start MongoDB service
# Windows: net start MongoDB
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod
```

**Option B: Docker MongoDB**
```bash
# Run MongoDB in Docker
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

**Option C: MongoDB Atlas (Cloud)**
- Sign up at [MongoDB Atlas](https://www.mongodb.com/atlas)
- Create a free cluster
- Get your connection string

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create or update your `.env` file with MongoDB settings:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories

# For MongoDB Atlas, use your connection string:
# MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
```

### Default Values

If no environment variables are set, the following defaults will be used:
- **MONGODB_URL**: `mongodb://localhost:27017`
- **MONGODB_DATABASE**: `slack2teams`
- **MONGODB_CHAT_COLLECTION**: `chat_histories`

## Migration Steps

### Step 1: Test MongoDB Connection

Before migrating, test that MongoDB is working:

```bash
python test_mongodb_integration.py
```

This will:
- Test MongoDB connection
- Verify basic operations
- Clean up test data

### Step 2: Backup Your Data

**Important**: Always backup your data before migration!

```bash
# Backup your existing chat history
cp data/chat_history.json data/chat_history_backup.json
```

### Step 3: Run Migration

Migrate your existing JSON data to MongoDB:

```bash
python migrate_to_mongodb.py
```

This script will:
- Read your existing `data/chat_history.json`
- Transfer all user conversations to MongoDB
- Preserve all message history and timestamps
- Show migration progress and results

### Step 4: Verify Migration

After migration, verify your data:

```bash
# Test the application
python server.py
```

Or run the test script again to verify everything is working.

## Data Structure

### JSON Format (Old)
```json
{
  "user_id": {
    "messages": [
      {
        "role": "user",
        "content": "Hello",
        "timestamp": "2025-10-21T17:24:04.981105"
      }
    ],
    "created_at": "2025-10-21T17:24:02.408015",
    "last_updated": "2025-10-21T17:24:04.981317"
  }
}
```

### MongoDB Format (New)
```json
{
  "_id": ObjectId("..."),
  "user_id": "user_id",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": ISODate("2025-10-21T17:24:04.981Z")
    }
  ],
  "created_at": ISODate("2025-10-21T17:24:02.408Z"),
  "last_updated": ISODate("2025-10-21T17:24:04.981Z")
}
```

## Troubleshooting

### Common Issues

**1. MongoDB Connection Failed**
```
❌ Failed to connect to MongoDB: [Errno 111] Connection refused
```
**Solution**: Ensure MongoDB is running and accessible at the configured URL.

**2. Authentication Failed**
```
❌ Failed to connect to MongoDB: Authentication failed
```
**Solution**: Check your MongoDB credentials and connection string.

**3. Migration Script Fails**
```
❌ Failed to migrate user user_id: ...
```
**Solution**: Check the error message and ensure your JSON file is valid.

### Getting Help

1. **Check MongoDB Status**:
   ```bash
   # Check if MongoDB is running
   mongo --eval "db.adminCommand('ping')"
   ```

2. **View MongoDB Logs**:
   ```bash
   # Check MongoDB logs for errors
   tail -f /var/log/mongodb/mongod.log
   ```

3. **Test Connection Manually**:
   ```python
   from motor.motor_asyncio import AsyncIOMotorClient
   import asyncio
   
   async def test():
       client = AsyncIOMotorClient("mongodb://localhost:27017")
       await client.admin.command('ping')
       print("Connection successful!")
   
   asyncio.run(test())
   ```

## Rollback (If Needed)

If you need to rollback to JSON storage:

1. **Revert endpoints.py**:
   ```python
   # Change this line back:
   from app.json_memory import add_to_conversation, get_conversation_context, get_user_chat_history, clear_user_chat_history
   ```

2. **Restore your backup**:
   ```bash
   cp data/chat_history_backup.json data/chat_history.json
   ```

3. **Restart your application**

## Benefits of MongoDB

- **Scalability**: Handle large amounts of chat data efficiently
- **Performance**: Faster queries and better indexing
- **Reliability**: ACID transactions and data durability
- **Flexibility**: Easy to add new fields or modify data structure
- **Backup**: Built-in backup and replication features
- **Monitoring**: Better tools for monitoring and debugging

## Next Steps

After successful migration:

1. **Monitor Performance**: Check application performance with MongoDB
2. **Set Up Backups**: Configure regular MongoDB backups
3. **Consider Indexing**: Add indexes for better query performance
4. **Clean Up**: Remove old JSON files after confirming everything works

## Support

If you encounter any issues during migration:

1. Check this guide for common solutions
2. Review the error messages carefully
3. Ensure MongoDB is properly configured and running
4. Test with the provided test scripts

Your chat history migration to MongoDB is now complete! 🎉
