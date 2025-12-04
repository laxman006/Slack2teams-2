# 🎯 Real User Questions System

## Overview

This system **automatically generates suggested questions from actual user chat history**, ensuring that the questions displayed to users are based on what people are really asking, not manually curated lists.

---

## 🔄 How It Works

```
┌─────────────────────────────────────────┐
│ Users Chat with Bot                     │
│ Questions stored in MongoDB             │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│ Analyzer Script Runs                    │
│ (Daily/Weekly/On-Demand)                │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│ Extract & Analyze User Questions        │
│ • Find valid questions                  │
│ • Count frequency                       │
│ • Remove duplicates                     │
│ • Categorize                            │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│ Update suggested_questions Collection   │
│ • Add new popular questions             │
│ • Update priorities                     │
│ • Track frequency                       │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│ Frontend Displays Questions             │
│ • Real user questions                   │
│ • Popular questions shown more          │
│ • Refreshes automatically               │
└─────────────────────────────────────────┘
```

---

## 📊 Data Source

### MongoDB Collection: `chat_histories`

```javascript
{
  "_id": ObjectId("..."),
  "user_id": "user@example.com",
  "messages": [
    {
      "role": "user",
      "content": "How do I migrate from Google Drive to OneDrive?",
      "timestamp": ISODate("2025-12-03T10:30:00Z")
    },
    {
      "role": "assistant",
      "content": "To migrate from Google Drive to OneDrive...",
      "timestamp": ISODate("2025-12-03T10:30:15Z")
    }
  ],
  "last_updated": ISODate("2025-12-03T10:30:15Z")
}
```

---

## 🚀 Usage

### 1. **Analyze User Questions (On-Demand)**

```bash
# Basic usage - analyze last 30 days
python -m scripts.analyze_user_questions

# Custom parameters
python -m scripts.analyze_user_questions --days 60 --min-freq 3 --limit 25

# Parameters:
#   --days: Days of history to analyze (default: 30)
#   --min-freq: Minimum times asked to include (default: 2)
#   --limit: Max questions to add/update (default: 20)
```

### 2. **Auto-Update (Scheduled)**

```bash
# Run auto-update with default settings
python -m scripts.auto_update_questions
```

**Schedule Options:**

#### Windows Task Scheduler:
```powershell
# Daily at 2 AM
schtasks /create /tn "Update Chat Questions" /tr "python C:\path\to\chatbot\scripts\auto_update_questions.py" /sc daily /st 02:00
```

#### Linux/Mac Cron:
```bash
# Add to crontab (daily at 2 AM)
0 2 * * * cd /path/to/chatbot && python -m scripts.auto_update_questions
```

---

## 🎯 Features

### 1. **Question Extraction**
- ✅ Only extracts valid questions (not statements)
- ✅ Filters by length (10-200 characters)
- ✅ Cleans and normalizes text
- ✅ Adds question marks where needed

### 2. **Frequency Analysis**
- ✅ Counts how many times each question was asked
- ✅ Prioritizes popular questions
- ✅ Minimum frequency threshold configurable

### 3. **Deduplication**
- ✅ Removes exact duplicates
- ✅ Merges similar questions (70% similarity threshold)
- ✅ Combines counts for similar questions

### 4. **Auto-Categorization**
- **Migration**: migrate, transfer, move, sync
- **Security**: security, encryption, safe, privacy
- **Pricing**: price, cost, plan, trial
- **Features**: feature, capability, support, option
- **Support**: help, problem, error, fail
- **Integration**: platform, integration, compatible
- **General**: everything else

### 5. **Priority Calculation**
```python
Priority = min(95, 50 + (frequency × 5))

Examples:
- Asked 1 time  → Priority 55
- Asked 5 times → Priority 75
- Asked 10 times → Priority 95 (max)
```

---

## 📈 Example Output

```
======================================================================
   ANALYZE USER QUESTIONS FROM CHAT HISTORY
======================================================================

📅 Analyzing questions from last 30 days
   (Since: 2025-11-03 14:38:19)

📊 Fetching chat histories from MongoDB...
✅ Processed 407 users, 1600 messages
✅ Found 632 valid user questions

📈 Analyzing question frequency...
✅ Found 328 questions asked 2+ times

🔍 Removing duplicate and similar questions...
✅ After deduplication: 312 unique questions

======================================================================
🎉 Analysis Complete!
======================================================================
   ✅ Added: 20 new questions
   🔄 Updated: 5 existing questions
   📊 Total in DB: 44
======================================================================

🔥 Top 10 Most Popular Questions:

 1. [50x] Does CloudFuze migrate Groups from Box to MS?
 2. [15x] What is CloudFuze?
 3. [14x] How do I migrate data from Slack to Microsoft Teams?
 4. [12x] Can CloudFuze migrate Slack custom emojis to Teams?
 5. [12x] What happens to file version history?
 ...
```

---

## 📊 Database Structure

### Collection: `suggested_questions`

```javascript
{
  "_id": ObjectId("..."),
  "question_text": "Does CloudFuze migrate Groups from Box to MS?",
  "category": "migration",
  "priority": 95,
  "keywords": ["cloudfuze", "migrate", "groups", "box"],
  "status": "active",
  
  // Analytics
  "display_count": 150,        // Times shown to users
  "click_count": 45,           // Times clicked
  "click_rate": 30.0,          // Calculated: (45/150) × 100
  
  // User history tracking
  "user_asked_count": 50,      // Times actually asked by users
  "source": "user_history",    // Or "manual_seed"
  
  // Metadata
  "created_at": ISODate("..."),
  "updated_at": ISODate("..."),
  "created_by": "auto_analyzer"
}
```

---

## 🎨 Frontend Display

Questions are displayed dynamically on the chat homepage:

```javascript
// Frontend fetches questions
GET /api/suggested-questions?limit=4

// Backend returns top 4 based on:
// 1. Priority (from frequency)
// 2. Click rate (user engagement)
// 3. Randomization (for variety)

// Response:
[
  {
    "id": "...",
    "question_text": "Does CloudFuze migrate Groups from Box to MS?",
    "category": "migration",
    "priority": 95,
    "click_rate": 30.0
  },
  ...
]
```

---

## 🔧 Maintenance

### View Current Questions

```javascript
// In MongoDB shell
use slack2teams
db.suggested_questions.find({status: "active"}).sort({priority: -1})
```

### Remove Low-Performing Questions

```javascript
// Questions with <1% click rate after 100+ displays
db.suggested_questions.updateMany(
  {
    display_count: {$gt: 100},
    click_rate: {$lt: 1.0}
  },
  {
    $set: {status: "inactive"}
  }
)
```

### Manually Add High-Priority Question

```javascript
db.suggested_questions.insertOne({
  question_text: "What's the Black Friday discount?",
  category: "pricing",
  priority: 100,
  keywords: ["black friday", "discount", "pricing"],
  status: "active",
  display_count: 0,
  click_count: 0,
  click_rate: 0.0,
  source: "manual",
  created_by: "admin",
  created_at: new Date(),
  updated_at: new Date()
})
```

---

## 📊 Analytics & Insights

### Most Popular Questions by Category

```javascript
db.suggested_questions.aggregate([
  {$match: {source: "user_history"}},
  {$group: {
    _id: "$category",
    total: {$sum: "$user_asked_count"},
    avg_priority: {$avg: "$priority"}
  }},
  {$sort: {total: -1}}
])
```

### Questions with Best Click-Through Rate

```javascript
db.suggested_questions.find(
  {display_count: {$gt: 50}},
  {question_text: 1, click_rate: 1}
).sort({click_rate: -1}).limit(10)
```

---

## 🎯 Benefits

### Compared to Manual Questions:

| Manual Questions | Auto-Generated (User History) |
|------------------|-------------------------------|
| ❌ Static/Outdated | ✅ Always current |
| ❌ Guesswork | ✅ Data-driven |
| ❌ Generic | ✅ Specific to your users |
| ❌ No engagement data | ✅ Tracks popularity |
| ❌ Requires code changes | ✅ Updates automatically |
| ❌ Same for everyone | ✅ Adapts to user needs |

---

## 🔮 Future Enhancements

### Possible Additions:

1. **Knowledge Base Relevance**
   - Use embeddings to filter questions by KB content
   - Only show questions that have good answers

2. **Personalized Questions**
   - Show questions based on user's role/industry
   - Track per-user preferences

3. **Seasonal Trends**
   - Detect trending questions this week/month
   - Show "Trending Now" section

4. **A/B Testing**
   - Test different question variations
   - Auto-optimize wording

5. **Smart Notifications**
   - Alert when new popular questions emerge
   - Weekly summary email to admin

---

## 🛠️ Troubleshooting

### No Questions Found

```bash
# Check if chat history exists
mongo
> use slack2teams
> db.chat_histories.count()
> db.chat_histories.findOne()
```

### Questions Not Updating

```bash
# Check last update time
> db.suggested_questions.find({source: "user_history"}).sort({updated_at: -1}).limit(1)

# Re-run analyzer
python -m scripts.analyze_user_questions --days 60 --min-freq 1
```

### Too Many Low-Quality Questions

```bash
# Increase minimum frequency
python -m scripts.analyze_user_questions --min-freq 5

# Or deactivate low performers
> db.suggested_questions.updateMany({priority: {$lt: 60}}, {$set: {status: "inactive"}})
```

---

## 📝 Summary

This system ensures your suggested questions are:

✅ **Real** - From actual user conversations  
✅ **Popular** - Based on frequency  
✅ **Current** - Auto-updates regularly  
✅ **Relevant** - Categorized and prioritized  
✅ **Engaging** - Tracks click-through rates  

**No more guessing what users want to ask!** 🎉

