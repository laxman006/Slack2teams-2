"""
Suggested Questions API Routes

Endpoints for managing and serving dynamic suggested questions.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import random

from app.models.suggested_question import (
    SuggestedQuestion,
    QuestionCreate,
    QuestionUpdate,
    QuestionAnalyticsUpdate,
    QuestionResponse,
    QuestionStatus,
    QuestionCategory
)
from app.mongodb_memory import mongodb_memory
from app.auth import verify_user_access

router = APIRouter(prefix="/api/suggested-questions", tags=["Suggested Questions"])


# ============================================================================
# PUBLIC ENDPOINTS (No auth required)
# ============================================================================

@router.get("/", response_model=List[QuestionResponse])
async def get_suggested_questions(
    limit: int = Query(default=4, ge=1, le=20, description="Number of questions to return"),
    category: Optional[QuestionCategory] = Query(None, description="Filter by category"),
    context: Optional[str] = Query(None, description="Context keywords for smart filtering")
):
    """
    Get suggested questions to display to users.
    
    **Smart Algorithm:**
    - Filters active questions
    - Optionally filters by category
    - Uses context keywords for relevance
    - Weights by priority and click-through rate
    - Returns randomized selection
    
    **Examples:**
    - GET /api/suggested-questions?limit=4
    - GET /api/suggested-questions?category=migration&limit=6
    - GET /api/suggested-questions?context=slack,teams&limit=4
    """
    # Ensure database connection is established
    if mongodb_memory.database is None:
        await mongodb_memory.connect()
    
    db = mongodb_memory.database
    
    if db is None:
        # Return default questions if DB connection fails
        return _get_default_questions(limit)
    
    # Build query
    query = {"status": QuestionStatus.ACTIVE.value}
    
    if category:
        query["category"] = category.value
    
    # Fetch questions
    cursor = db.suggested_questions.find(query)
    questions = await cursor.to_list(length=None)
    
    if not questions:
        # Return default fallback questions if none in DB
        return _get_default_questions(limit)
    
    # Context-aware filtering
    if context and questions:
        context_keywords = [k.strip().lower() for k in context.split(',')]
        
        # Score questions based on keyword matching
        scored_questions = []
        for q in questions:
            score = q.get('priority', 50)
            
            # Boost score if keywords match
            q_keywords = q.get('keywords', [])
            if q_keywords:
                matching_keywords = set(context_keywords) & set([k.lower() for k in q_keywords])
                score += len(matching_keywords) * 20
            
            # Boost high-performing questions
            click_rate = q.get('click_rate', 0)
            score += click_rate * 0.5
            
            scored_questions.append((score, q))
        
        # Sort by score and take top candidates
        scored_questions.sort(reverse=True, key=lambda x: x[0])
        questions = [q for _, q in scored_questions[:limit * 2]]  # Take 2x for randomization
    
    # Randomize from top candidates (ensure no duplicates)
    if len(questions) > limit:
        # Use sample for no duplicates, then sort by priority to maintain quality
        available_pool = questions[:min(len(questions), limit * 3)]  # Top 3x for better variety
        selected = random.sample(available_pool, min(limit, len(available_pool)))
    else:
        selected = questions[:limit]
    
    # Update display count asynchronously
    for q in selected:
        await db.suggested_questions.update_one(
            {"_id": q["_id"]},
            {
                "$inc": {"display_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    # Format response
    return [
        QuestionResponse(
            id=str(q["_id"]),
            question_text=q["question_text"],
            category=q.get("category", "general"),
            priority=q.get("priority", 50),
            click_rate=q.get("click_rate", 0.0)
        )
        for q in selected
    ]


@router.post("/analytics")
async def track_question_analytics(data: QuestionAnalyticsUpdate):
    """
    Track analytics for question displays and clicks.
    
    **Actions:**
    - `display`: Question was shown to user
    - `click`: User clicked the question
    
    This helps optimize which questions to show.
    """
    # Ensure database connection is established
    if mongodb_memory.database is None:
        await mongodb_memory.connect()
    
    db = mongodb_memory.database
    
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        question_id = ObjectId(data.question_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid question ID")
    
    question = await db.suggested_questions.find_one({"_id": question_id})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    update_data = {"updated_at": datetime.utcnow()}
    
    if data.action == "display":
        update_data["$inc"] = {"display_count": 1}
    elif data.action == "click":
        update_data["$inc"] = {"click_count": 1}
        
        # Recalculate click rate
        new_click_count = question.get("click_count", 0) + 1
        display_count = question.get("display_count", 1)
        click_rate = (new_click_count / display_count) * 100 if display_count > 0 else 0
        update_data["$set"] = {"click_rate": round(click_rate, 2), "updated_at": datetime.utcnow()}
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'display' or 'click'")
    
    await db.suggested_questions.update_one({"_id": question_id}, update_data)
    
    return {"success": True, "message": f"Analytics updated for action: {data.action}"}


# ============================================================================
# ADMIN ENDPOINTS (Auth required)
# ============================================================================

@router.post("/admin", response_model=QuestionResponse, dependencies=[Depends(verify_user_access)])
async def create_question(question: QuestionCreate, current_user=Depends(verify_user_access)):
    """
    **[ADMIN]** Create a new suggested question.
    
    Only authenticated users can create questions.
    """
    if mongodb_memory.database is None:
        await mongodb_memory.connect()
    
    db = mongodb_memory.database
    
    # Check if question already exists
    existing = await db.suggested_questions.find_one({"question_text": question.question_text})
    if existing:
        raise HTTPException(status_code=400, detail="Question already exists")
    
    # Create question document
    question_doc = {
        "question_text": question.question_text,
        "category": question.category.value,
        "status": QuestionStatus.ACTIVE.value,
        "priority": question.priority,
        "keywords": question.keywords or [],
        "target_user_roles": question.target_user_roles or [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": current_user.get("id"),
        "display_count": 0,
        "click_count": 0,
        "click_rate": 0.0
    }
    
    result = await db.suggested_questions.insert_one(question_doc)
    question_doc["_id"] = result.inserted_id
    
    return QuestionResponse(
        id=str(question_doc["_id"]),
        question_text=question_doc["question_text"],
        category=question_doc["category"],
        priority=question_doc["priority"],
        click_rate=0.0
    )


@router.get("/admin/all", dependencies=[Depends(verify_user_access)])
async def get_all_questions(
    status: Optional[QuestionStatus] = Query(None),
    category: Optional[QuestionCategory] = Query(None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100)
):
    """
    **[ADMIN]** Get all questions with filtering and pagination.
    """
    if mongodb_memory.database is None:
        await mongodb_memory.connect()
    
    db = mongodb_memory.database
    
    query = {}
    if status:
        query["status"] = status.value
    if category:
        query["category"] = category.value
    
    total = await db.suggested_questions.count_documents(query)
    cursor = db.suggested_questions.find(query).skip(skip).limit(limit).sort("priority", -1)
    questions = await cursor.to_list(length=limit)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "questions": [
            {
                "id": str(q["_id"]),
                "question_text": q["question_text"],
                "category": q.get("category"),
                "status": q.get("status"),
                "priority": q.get("priority"),
                "display_count": q.get("display_count", 0),
                "click_count": q.get("click_count", 0),
                "click_rate": q.get("click_rate", 0.0),
                "created_at": q.get("created_at"),
                "updated_at": q.get("updated_at")
            }
            for q in questions
        ]
    }


@router.put("/admin/{question_id}", dependencies=[Depends(verify_user_access)])
async def update_question(question_id: str, update_data: QuestionUpdate):
    """
    **[ADMIN]** Update a suggested question.
    """
    if mongodb_memory.database is None:
        await mongodb_memory.connect()
    
    db = mongodb_memory.database
    
    try:
        q_id = ObjectId(question_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid question ID")
    
    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}
    if update_data.question_text:
        update_doc["question_text"] = update_data.question_text
    if update_data.category:
        update_doc["category"] = update_data.category.value
    if update_data.status:
        update_doc["status"] = update_data.status.value
    if update_data.priority is not None:
        update_doc["priority"] = update_data.priority
    if update_data.keywords is not None:
        update_doc["keywords"] = update_data.keywords
    if update_data.target_user_roles is not None:
        update_doc["target_user_roles"] = update_data.target_user_roles
    
    result = await db.suggested_questions.update_one({"_id": q_id}, {"$set": update_doc})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"success": True, "message": "Question updated successfully"}


@router.delete("/admin/{question_id}", dependencies=[Depends(verify_user_access)])
async def delete_question(question_id: str):
    """
    **[ADMIN]** Delete a suggested question.
    """
    if mongodb_memory.database is None:
        await mongodb_memory.connect()
    
    db = mongodb_memory.database
    
    try:
        q_id = ObjectId(question_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid question ID")
    
    result = await db.suggested_questions.delete_one({"_id": q_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"success": True, "message": "Question deleted successfully"}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_default_questions(limit: int = 4) -> List[QuestionResponse]:
    """Return default fallback questions if DB is empty"""
    default_questions = [
        QuestionResponse(
            id="default-1",
            question_text="How do I migrate data from Slack to Microsoft Teams?",
            category="migration",
            priority=80,
            click_rate=0.0
        ),
        QuestionResponse(
            id="default-2",
            question_text="What are the best practices for cloud migration?",
            category="migration",
            priority=75,
            click_rate=0.0
        ),
        QuestionResponse(
            id="default-3",
            question_text="How can I track migration progress?",
            category="features",
            priority=70,
            click_rate=0.0
        ),
        QuestionResponse(
            id="default-4",
            question_text="What are the key features of CloudFuze?",
            category="features",
            priority=65,
            click_rate=0.0
        ),
        QuestionResponse(
            id="default-5",
            question_text="How does CloudFuze pricing work?",
            category="pricing",
            priority=60,
            click_rate=0.0
        ),
        QuestionResponse(
            id="default-6",
            question_text="What platforms does CloudFuze support?",
            category="integration",
            priority=55,
            click_rate=0.0
        )
    ]
    
    return random.sample(default_questions, min(limit, len(default_questions)))

