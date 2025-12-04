# 🎯 Dynamic Suggested Questions System

## Overview

This system replaces hardcoded suggested questions with a dynamic, data-driven approach that allows:
- ✅ **Dynamic Updates** - Change questions without code changes
- ✅ **Analytics Tracking** - Track which questions perform best
- ✅ **Context-Aware** - Show relevant questions based on user context
- ✅ **A/B Testing** - Test different questions and measure effectiveness
- ✅ **User Submissions** - Allow users to suggest questions (future)

---

## 🏗️ Architecture

```
┌──────────────────┐
│   Frontend       │
│  (React/Next.js) │
└────────┬─────────┘
         │ GET /api/suggested-questions
         ▼
┌──────────────────┐
│  Backend API     │
│  (FastAPI)       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   MongoDB        │
│  - Questions     │
│  - Analytics     │
└──────────────────┘
```

---

## 📊 Database Schema

### Collection: `suggested_questions`

```javascript
{
  "_id": ObjectId("..."),
  "question_text": "How do I migrate data from Slack to Microsoft Teams?",
  "category": "migration",  // migration, features, pricing, etc.
  "status": "active",  // active, inactive, pending, rejected
  "priority": 80,  // 0-100, higher = more likely to show
  
  // Analytics
  "display_count": 1250,  // Times shown
  "click_count": 87,  // Times clicked
  "click_rate": 6.96,  // Percentage
  
  // Targeting (optional)
  "keywords": ["slack", "teams", "migration"],
  "target_user_roles": [],  // Show only to specific roles
  
  // Metadata
  "created_at": ISODate("..."),
  "updated_at": ISODate("..."),
  "created_by": "admin_user_id"
}
```

---

## 🚀 Setup Instructions

### 1. Seed Initial Questions

Run the seed script to populate your database with initial questions:

```bash
cd chatbot
python -m scripts.seed_suggested_questions
```

This will add ~18 high-quality questions across different categories.

### 2. Update Frontend

Replace hardcoded questions with dynamic fetching:

**File: `frontend/src/app/page.tsx`**

Add this function inside `initializeChatApp()`:

```typescript
// Fetch dynamic suggested questions from API
async function loadSuggestedQuestions() {
  try {
    const response = await fetch(`${getApiBase()}/api/suggested-questions?limit=4`);
    if (!response.ok) {
      console.error('[QUESTIONS] Failed to load questions');
      return;
    }
    
    const questions = await response.json();
    updateSuggestedQuestions(questions);
  } catch (error) {
    console.error('[QUESTIONS] Error loading questions:', error);
  }
}

// Update suggested questions in both locations
function updateSuggestedQuestions(questions: any[]) {
  const containers = document.querySelectorAll('.suggested-questions-container');
  
  containers.forEach(container => {
    if (!questions || questions.length === 0) return;
    
    const html = questions.map(q => `
      <button class="suggested-question-btn" 
              data-question="${q.question_text.replace(/"/g, '&quot;')}"
              data-question-id="${q.id}"
              onclick="trackQuestionClick('${q.id}')">
        ${q.question_text}
      </button>
    `).join('');
    
    container.innerHTML = html;
  });
  
  // Re-attach event listeners
  attachSuggestedQuestionListeners();
}

// Track question clicks for analytics
function trackQuestionClick(questionId: string) {
  fetch(`${getApiBase()}/api/suggested-questions/analytics`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action: 'click',
      question_id: questionId
    })
  }).catch(err => console.error('[ANALYTICS] Failed to track click:', err));
}

// Expose to window
(window as any).trackQuestionClick = trackQuestionClick;

// Call on page load
loadSuggestedQuestions();
```

### 3. Replace Hardcoded HTML

Find these two sections in your JSX and update them:

```tsx
{/* Empty State Suggested Questions */}
<div className="suggested-questions-container">
  {/* Questions will be loaded dynamically */}
</div>

{/* Bottom Input Suggested Questions */}
<div className="suggested-questions-container">
  {/* Questions will be loaded dynamically */}
</div>
```

---

## 📡 API Endpoints

### Public Endpoints (No Auth)

#### GET /api/suggested-questions

Get questions to display to users.

**Query Parameters:**
- `limit` (int): Number of questions (1-20, default: 4)
- `category` (str): Filter by category
- `context` (str): Comma-separated keywords for relevance

**Examples:**

```bash
# Get 4 random high-priority questions
curl http://localhost:8002/api/suggested-questions?limit=4

# Get migration-related questions
curl http://localhost:8002/api/suggested-questions?category=migration

# Get context-aware questions
curl http://localhost:8002/api/suggested-questions?context=slack,teams&limit=4
```

**Response:**

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "question_text": "How do I migrate data from Slack to Microsoft Teams?",
    "category": "migration",
    "priority": 90,
    "click_rate": 7.5
  }
]
```

#### POST /api/suggested-questions/analytics

Track question analytics (displays and clicks).

**Request Body:**

```json
{
  "action": "click",  // or "display"
  "question_id": "507f1f77bcf86cd799439011"
}
```

### Admin Endpoints (Auth Required)

#### POST /api/suggested-questions/admin

Create a new question.

```json
{
  "question_text": "How do I migrate Trello boards to Asana?",
  "category": "migration",
  "priority": 75,
  "keywords": ["trello", "asana", "migration", "project management"]
}
```

#### GET /api/suggested-questions/admin/all

Get all questions with filters and pagination.

**Query Parameters:**
- `status`: Filter by status (active, inactive, pending, rejected)
- `category`: Filter by category
- `skip`: Skip N records (pagination)
- `limit`: Limit results (1-100, default: 50)

#### PUT /api/suggested-questions/admin/{question_id}

Update a question.

```json
{
  "status": "inactive",
  "priority": 60
}
```

#### DELETE /api/suggested-questions/admin/{question_id}

Delete a question.

---

## 📈 Smart Algorithm

The system uses a sophisticated algorithm to select questions:

### 1. **Filtering**
- Only active questions
- Optional category filter
- Optional keyword matching

### 2. **Scoring**
```
Question Score = Base Priority 
                + (Keyword Matches × 20)
                + (Click Rate × 0.5)
```

### 3. **Selection**
- Take top-scoring candidates (2x desired limit)
- Weighted random selection based on priority
- Returns requested number of questions

### 4. **Analytics**
- Tracks every display automatically
- Tracks clicks when user interacts
- Calculates click-through rate
- Updates in real-time

---

## 💡 Usage Examples

### Example 1: Basic Usage

Show 4 general questions:

```javascript
fetch('/api/suggested-questions?limit=4')
  .then(res => res.json())
  .then(questions => {
    // Display questions in UI
    displayQuestions(questions);
  });
```

### Example 2: Context-Aware Questions

Show questions relevant to current conversation:

```javascript
// User is asking about Slack migration
const context = "slack,migration,teams";

fetch(`/api/suggested-questions?context=${context}&limit=4`)
  .then(res => res.json())
  .then(questions => {
    // Will prioritize migration and Slack-related questions
    displayQuestions(questions);
  });
```

### Example 3: Category-Specific

Show only pricing questions:

```javascript
fetch('/api/suggested-questions?category=pricing&limit=3')
  .then(res => res.json())
  .then(questions => {
    displayQuestions(questions);
  });
```

---

## 🎨 Admin Interface (Future)

A web-based admin panel can be built to manage questions:

### Features:
- ✅ **CRUD Operations** - Create, Read, Update, Delete questions
- ✅ **Analytics Dashboard** - View performance metrics
- ✅ **Bulk Operations** - Activate/deactivate multiple questions
- ✅ **Preview Mode** - Test questions before going live
- ✅ **A/B Testing** - Compare question variations
- ✅ **User Submissions** - Review and approve user-suggested questions

### Mockup:

```
┌─────────────────────────────────────────────────────┐
│  Suggested Questions Admin                          │
├─────────────────────────────────────────────────────┤
│  [+ New Question]  [Import]  [Export]               │
│                                                      │
│  Filters: [All Categories ▼] [Active ▼]            │
│                                                      │
│  ┌────────────────────────────────────────────────┐│
│  │ Question                          Stats Actions ││
│  ├────────────────────────────────────────────────┤│
│  │ How do I migrate from Slack...   1.2K  87  [Edit] [Delete] ││
│  │ Category: Migration  Priority: 90  CTR: 7.2%   ││
│  ├────────────────────────────────────────────────┤│
│  │ What are CloudFuze's features?   980   45  [Edit] [Delete] ││
│  │ Category: Features   Priority: 85  CTR: 4.6%   ││
│  └────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

## 🔍 Analytics Insights

Track and optimize question performance:

### Key Metrics:

1. **Display Count** - How many times shown
2. **Click Count** - How many times clicked
3. **Click-Through Rate (CTR)** - (Clicks / Displays) × 100
4. **Priority Score** - Admin-set importance (0-100)

### Optimization Strategy:

```
High CTR (>5%) + High Priority = ⭐ Keep showing
High CTR + Low Priority = 📈 Increase priority
Low CTR (<2%) + High Priority = 🔍 Review/modify
Low CTR + Low Priority = 🗑️ Consider removing
```

---

## 🚀 Next Steps

### Phase 1: Basic Implementation ✅
- [x] Database schema
- [x] API endpoints
- [x] Seed script
- [ ] Frontend integration

### Phase 2: Analytics 📊
- [ ] Click tracking implementation
- [ ] Analytics dashboard
- [ ] Performance reports

### Phase 3: Intelligence 🧠
- [ ] AI-powered question generation
- [ ] Contextual question selection based on chat history
- [ ] Personalized questions per user

### Phase 4: User Engagement 👥
- [ ] User-submitted questions
- [ ] Voting system
- [ ] Community-driven questions

### Phase 5: Admin Interface 🎨
- [ ] Web-based admin panel
- [ ] Visual analytics
- [ ] A/B testing framework

---

## 🛠️ Troubleshooting

### Questions not showing?

1. Check if seed script ran successfully:
```bash
python -m scripts.seed_suggested_questions
```

2. Verify database connection:
```bash
# In Python
from app.mongodb_memory import mongodb_memory
mongodb_memory.db.suggested_questions.count_documents({})
```

3. Check API endpoint:
```bash
curl http://localhost:8002/api/suggested-questions?limit=4
```

### Analytics not tracking?

Ensure the `trackQuestionClick()` function is called on click and the analytics endpoint is reachable.

---

## 📝 Best Practices

### Writing Good Questions:

✅ **DO:**
- Keep questions concise (< 80 characters)
- Make them action-oriented
- Focus on common user needs
- Use clear, simple language

❌ **DON'T:**
- Use technical jargon unnecessarily
- Make questions too vague
- Repeat similar questions
- Use ambiguous wording

### Examples:

✅ Good: "How do I migrate from Slack to Teams?"
❌ Bad: "What are the considerations regarding the migration process from Slack?"

---

## 🎯 Success Metrics

Track these KPIs to measure success:

1. **Question CTR** - Target: > 5%
2. **User Engagement** - % of users clicking suggestions
3. **Question Diversity** - Coverage across categories
4. **Update Frequency** - How often questions are refreshed
5. **User Satisfaction** - Feedback on question relevance

---

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Queries](https://docs.mongodb.com/manual/tutorial/query-documents/)
- [Next.js Data Fetching](https://nextjs.org/docs/basic-features/data-fetching)

---

**Questions or Issues?**  
Contact the development team or open an issue in the repository.

