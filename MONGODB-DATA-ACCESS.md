# MongoDB Data Access Guide

## All Your Data is Now in MongoDB Atlas! 🎉

After running the migration, **all your data** is stored in MongoDB Atlas cloud database.

---

## 📊 MongoDB Collections

### Your Database: `slack2teams`

| Collection | Documents | Purpose |
|-----------|-----------|---------|
| `cloudfuze_vectorstore` | 1,511 | 🌐 Vector embeddings (chatbot knowledge) |
| `chat_histories` | 19+ | 💬 User conversations |
| `fine_tuning_data` | 110+ | 🎓 Training corrections & data |
| `fine_tuning_status` | 1 | 🎓 Current fine-tuning job |
| `feedback_history` | 1+ | 👍 User feedback (thumbs up/down) |
| `corrected_responses` | Multiple | ✏️ Manual corrections |
| `bad_responses` | Multiple | 🐛 Error traces for debugging |
| `vectorstore_metadata` | 1 | 📋 Vector store metadata |

**Total**: Everything that was in `./data/` folder!

---

## 🔧 How to Access Data in Your Code

### Import the Manager

```python
from app.mongodb_data_manager import mongodb_data

# Or use helper functions
from app.mongodb_data_manager import (
    get_corrections_for_finetuning,
    save_correction,
    log_bad_response
)
```

### Examples

#### 1. Get Fine-Tuning Corrections

```python
# Get all corrections
corrections = mongodb_data.get_corrections()
print(f"Found {len(corrections)} corrections")

# Get in OpenAI format (ready for fine-tuning)
from app.mongodb_data_manager import get_corrections_for_finetuning
training_data = get_corrections_for_finetuning()
```

#### 2. Add New Correction

```python
from app.mongodb_data_manager import save_correction

save_correction(
    user_query="What is CloudFuze?",
    bad_response="I don't know",
    good_response="CloudFuze is a cloud migration platform...",
    user_id="user123"
)
```

#### 3. Get Feedback Statistics

```python
stats = mongodb_data.get_feedback_stats()
print(f"Total feedback: {stats['total']}")
print(f"Positive rate: {stats['positive_rate']:.1f}%")
```

#### 4. Check Fine-Tuning Status

```python
status = mongodb_data.get_fine_tuning_status()
print(f"Job ID: {status['job_id']}")
print(f"Status: {status['status']}")
```

#### 5. Log Bad Response

```python
from app.mongodb_data_manager import log_bad_response

log_bad_response(
    query="Test query",
    response="Bad response",
    error="Hallucination detected",
    user_id="user123"
)
```

#### 6. Get All Statistics

```python
stats = mongodb_data.get_all_stats()
print(f"Fine-tuning corrections: {stats['fine_tuning_corrections']}")
print(f"Feedback items: {stats['feedback_items']}")
print(f"Vector documents: {stats['vector_documents']}")
```

---

## 🚀 Updating Your Application

### Before (Local Files):

```python
# OLD - Reading from local file
with open('./data/fine_tuning_dataset/corrections.jsonl', 'r') as f:
    corrections = [json.loads(line) for line in f]
```

### After (MongoDB):

```python
# NEW - Reading from MongoDB
from app.mongodb_data_manager import mongodb_data
corrections = mongodb_data.get_corrections()
```

---

## 📁 What About Local Files?

### After Successful Migration:

1. **Keep as backup** (recommended initially):
   ```bash
   # Rename to backup
   mv data data_backup_20251028
   ```

2. **Or create minimal data folder** (for file uploads, temp files):
   ```bash
   mkdir data
   # Keep only what you need for temporary files
   ```

3. **Clean up completely** (after testing):
   ```bash
   # Only after verifying everything works!
   rm -rf data/chroma_db/  # Old vector store
   rm -rf data/fine_tuning_dataset/  # Now in MongoDB
   rm data/fine_tuning_status.json  # Now in MongoDB
   # etc.
   ```

---

## 🔍 Viewing Data in MongoDB Atlas

### Web Interface

1. Go to https://cloud.mongodb.com
2. Navigate to: **Clusters** → **Browse Collections**
3. Select database: `slack2teams`
4. Browse your collections!

### Example Queries

#### View Fine-Tuning Corrections
```javascript
// In MongoDB Atlas web interface
db.fine_tuning_data.find({type: "correction"})
```

#### View Recent Feedback
```javascript
db.feedback_history.find().sort({created_at: -1}).limit(10)
```

#### Count All Data
```javascript
db.getCollectionNames().forEach(function(col) {
    print(col + ": " + db[col].count());
});
```

---

## 📊 Data Structure Examples

### Fine-Tuning Correction

```json
{
  "_id": ObjectId("..."),
  "type": "correction",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "What is CloudFuze?"},
    {"role": "assistant", "content": "CloudFuze is..."}
  ],
  "metadata": {
    "user_id": "user123",
    "bad_response": "I don't know",
    "corrected_at": "2025-10-28T..."
  },
  "created_at": ISODate("2025-10-28T..."),
  "migrated_at": ISODate("2025-10-28T...")
}
```

### Feedback Item

```json
{
  "_id": ObjectId("..."),
  "user_id": "user123",
  "rating": "positive",
  "message": "Great answer!",
  "query": "What is CloudFuze?",
  "response": "CloudFuze is...",
  "created_at": ISODate("2025-10-28T...")
}
```

### Fine-Tuning Status

```json
{
  "_id": ObjectId("..."),
  "job_id": "ftjob-lKgljXCOxBpQCWnHnhsoryOC",
  "status": "validating_files",
  "model": "gpt-4o-mini-2024-07-18",
  "training_file_id": "file-GexdZFT8o9KEurdBve5Khj",
  "created_at": "2025-10-24T19:19:54",
  "training_examples": 55,
  "updated_at": ISODate("2025-10-28T...")
}
```

---

## 🔄 Updating Existing Scripts

### Fine-Tuning Script Update

```python
# OLD: scripts/finetune_unified.py
def load_corrections():
    with open('./data/fine_tuning_dataset/corrections.jsonl', 'r') as f:
        return [json.loads(line) for line in f]

# NEW: Use MongoDB
from app.mongodb_data_manager import mongodb_data

def load_corrections():
    return mongodb_data.get_corrections()
```

### Feedback Collection Update

```python
# OLD: app/endpoints.py
def save_feedback(feedback_data):
    with open('./data/feedback_history.json', 'r+') as f:
        data = json.load(f)
        data[user_id].append(feedback_data)
        f.write(json.dumps(data))

# NEW: Use MongoDB
from app.mongodb_data_manager import mongodb_data

def save_feedback(feedback_data):
    mongodb_data.add_feedback(feedback_data)
```

---

## 🎯 Benefits of MongoDB Storage

✅ **No File Management** - No need to manage local files  
✅ **Automatic Backups** - MongoDB Atlas handles backups  
✅ **Real-time Sync** - Multiple servers can access same data  
✅ **Better Queries** - Powerful search and filtering  
✅ **Scalability** - Handles growth automatically  
✅ **Cloud Access** - Access from anywhere  
✅ **No Git Conflicts** - No more merge conflicts with data files  

---

## 🔧 Advanced Usage

### Custom Queries

```python
from app.mongodb_data_manager import mongodb_data

# Get corrections from last 7 days
from datetime import datetime, timedelta
week_ago = datetime.utcnow() - timedelta(days=7)

recent_corrections = list(
    mongodb_data.db["fine_tuning_data"].find({
        "type": "correction",
        "created_at": {"$gte": week_ago}
    })
)

# Get negative feedback only
negative_feedback = list(
    mongodb_data.db["feedback_history"].find({
        "rating": "negative"
    })
)

# Count responses by user
pipeline = [
    {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
user_stats = list(
    mongodb_data.db["chat_histories"].aggregate(pipeline)
)
```

### Exporting Data

```python
from app.mongodb_data_manager import mongodb_data
import json

# Export corrections for backup
corrections = mongodb_data.get_corrections()
with open('corrections_backup.json', 'w') as f:
    json.dump(corrections, f, indent=2, default=str)
```

---

## 🆘 Troubleshooting

### Issue: "Cannot connect to MongoDB"

**Solution**: Check your `.env` file has correct `MONGODB_URL`

### Issue: "Collection not found"

**Solution**: Run the migration script first:
```bash
python migrate_all_to_mongodb.py
```

### Issue: "Want to rollback to local files"

**Solution**: 
1. Keep your `data_backup` folder
2. Copy files back to `./data/`
3. Update code to use file access again

---

## 📚 Summary

**All your data is now centralized in MongoDB Atlas:**

- ✅ Vector embeddings → `cloudfuze_vectorstore`
- ✅ Chat history → `chat_histories`
- ✅ Fine-tuning data → `fine_tuning_data`
- ✅ Feedback → `feedback_history`
- ✅ Corrections → `corrected_responses`
- ✅ Error traces → `bad_responses`
- ✅ Metadata → `vectorstore_metadata`

**No more local file management needed!** 🎉

---

**Need help?** Check the MongoDB Atlas documentation or use the helper functions in `app/mongodb_data_manager.py`



