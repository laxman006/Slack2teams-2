"""
Suggested Questions API Routes

Endpoints for managing and serving dynamic suggested questions.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import random
import logging

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

# Configure logging
logger = logging.getLogger(__name__)

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
    - ALWAYS returns questions (uses fallback if DB fails)
    
    **Examples:**
    - GET /api/suggested-questions?limit=4
    - GET /api/suggested-questions?category=migration&limit=6
    - GET /api/suggested-questions?context=slack,teams&limit=4
    """
    logger.info(f"[QUESTIONS] Request received - limit={limit}, category={category}, context={context}")
    
    try:
        # Ensure database connection is established
        logger.debug("[QUESTIONS] Checking MongoDB connection...")
        if mongodb_memory.database is None:
            logger.info("[QUESTIONS] MongoDB not connected, attempting connection...")
            await mongodb_memory.connect()
        
        db = mongodb_memory.database
        
        if db is None:
            # Return default questions if DB connection fails
            logger.warning("[QUESTIONS] ❌ DB connection failed, using fallback questions")
            fallback_questions = _get_default_questions(limit)
            logger.info(f"[QUESTIONS] ✅ Returning {len(fallback_questions)} fallback questions")
            return fallback_questions
        
        logger.info("[QUESTIONS] ✅ MongoDB connection successful")
        
        # Build query
        query = {"status": QuestionStatus.ACTIVE.value}
        
        if category:
            query["category"] = category.value
            logger.debug(f"[QUESTIONS] Filtering by category: {category.value}")
        
        logger.debug(f"[QUESTIONS] Query: {query}")
        
        # Fetch questions
        logger.debug("[QUESTIONS] Fetching questions from database...")
        cursor = db.suggested_questions.find(query)
        questions = await cursor.to_list(length=None)
        
        logger.info(f"[QUESTIONS] Found {len(questions)} active questions in database")
        
        if not questions:
            # Return default fallback questions if none in DB
            logger.warning("[QUESTIONS] ⚠️  No questions in DB, using fallback questions")
            fallback_questions = _get_default_questions(limit)
            logger.info(f"[QUESTIONS] ✅ Returning {len(fallback_questions)} fallback questions")
            return fallback_questions
        
        # Context-aware filtering
        if context and questions:
            context_keywords = [k.strip().lower() for k in context.split(',')]
            logger.debug(f"[QUESTIONS] Context filtering with keywords: {context_keywords}")
            
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
            logger.debug(f"[QUESTIONS] After context filtering: {len(questions)} candidates")
        
        # Randomize from top candidates (ensure no duplicates)
        if len(questions) > limit:
            # Use sample for no duplicates, then sort by priority to maintain quality
            available_pool = questions[:min(len(questions), limit * 3)]  # Top 3x for better variety
            selected = random.sample(available_pool, min(limit, len(available_pool)))
            logger.debug(f"[QUESTIONS] Randomly selected {len(selected)} from {len(available_pool)} candidates")
        else:
            selected = questions[:limit]
            logger.debug(f"[QUESTIONS] Selected all {len(selected)} questions (pool size <= limit)")
        
        # Log selected questions
        logger.info(f"[QUESTIONS] Selected {len(selected)} questions:")
        for i, q in enumerate(selected, 1):
            logger.info(f"  {i}. [{q.get('priority', 50)}] {q.get('question_text', 'N/A')[:60]}...")
        
        # Update display count asynchronously (don't fail if this errors)
        try:
            update_count = 0
            for q in selected:
                await db.suggested_questions.update_one(
                    {"_id": q["_id"]},
                    {
                        "$inc": {"display_count": 1},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
                update_count += 1
            logger.debug(f"[QUESTIONS] Updated display_count for {update_count} questions")
        except Exception as update_error:
            logger.warning(f"[QUESTIONS] ⚠️  Failed to update display count: {update_error}")
        
        # Format response
        response = [
            QuestionResponse(
                id=str(q["_id"]),
                question_text=q["question_text"],
                category=q.get("category", "general"),
                priority=q.get("priority", 50),
                click_rate=q.get("click_rate", 0.0)
            )
            for q in selected
        ]
        
        logger.info(f"[QUESTIONS] ✅ Successfully returning {len(response)} questions from database")
        return response
    
    except Exception as e:
        # CRITICAL: Always return questions, even on error
        logger.error(f"[QUESTIONS] ❌ Error fetching from DB: {type(e).__name__}: {e}", exc_info=True)
        logger.warning("[QUESTIONS] Using fallback questions due to error")
        fallback_questions = _get_default_questions(limit)
        logger.info(f"[QUESTIONS] ✅ Returning {len(fallback_questions)} fallback questions")
        return fallback_questions


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
    """Return default fallback questions if DB is empty or connection fails.
    
    This ensures questions ALWAYS show, even if MongoDB is unavailable.
    Questions are randomly selected from a comprehensive pool.
    """
    # Comprehensive fallback question pool (matches seed script)
    default_questions = [
        # Top Priority Questions (90-95)
        QuestionResponse(
            id="fallback-1",
            question_text="How do I migrate from Google Drive to OneDrive?",
            category="migration",
            priority=95,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-2",
            question_text="Can I migrate Slack channels to Microsoft Teams?",
            category="migration",
            priority=92,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-3",
            question_text="How secure is my data during migration?",
            category="security",
            priority=90,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-4",
            question_text="What's the fastest way to migrate SharePoint Online?",
            category="migration",
            priority=88,
            click_rate=0.0
        ),
        # High Priority Questions (80-89)
        QuestionResponse(
            id="fallback-5",
            question_text="Can I migrate from Box to Google Drive?",
            category="migration",
            priority=85,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-6",
            question_text="How do I preserve permissions during migration?",
            category="features",
            priority=83,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-7",
            question_text="Can I schedule migrations to run automatically?",
            category="features",
            priority=80,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-8",
            question_text="How do I track my migration progress?",
            category="features",
            priority=80,
            click_rate=0.0
        ),
        # Medium-High Priority Questions (70-79)
        QuestionResponse(
            id="fallback-9",
            question_text="Which cloud platforms does CloudFuze support?",
            category="integration",
            priority=78,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-10",
            question_text="Can I migrate large files over 5GB?",
            category="features",
            priority=75,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-11",
            question_text="How long does a typical migration take?",
            category="general",
            priority=73,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-12",
            question_text="Can I do a trial migration before the full migration?",
            category="features",
            priority=70,
            click_rate=0.0
        ),
        # Additional Popular Questions
        QuestionResponse(
            id="fallback-13",
            question_text="Does CloudFuze support Office 365 tenant-to-tenant migration?",
            category="migration",
            priority=86,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-14",
            question_text="Can I migrate Gmail to Office 365?",
            category="migration",
            priority=84,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-15",
            question_text="What happens if my migration fails?",
            category="support",
            priority=82,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-16",
            question_text="How do I migrate from Dropbox Business to SharePoint?",
            category="migration",
            priority=81,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-17",
            question_text="Can CloudFuze migrate Google Workspace to Microsoft 365?",
            category="migration",
            priority=87,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-18",
            question_text="Will metadata and timestamps be preserved?",
            category="features",
            priority=72,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-19",
            question_text="Can I migrate incremental changes after initial migration?",
            category="features",
            priority=77,
            click_rate=0.0
        ),
        QuestionResponse(
            id="fallback-20",
            question_text="What's included in the free trial?",
            category="pricing",
            priority=68,
            click_rate=0.0
        ),
    ]
    
    # Randomly select questions, ensuring variety
    # Sort by priority first, then randomize from top candidates
    sorted_questions = sorted(default_questions, key=lambda x: x.priority, reverse=True)
    
    # Take top 2x limit for better variety, then randomize
    top_candidates = sorted_questions[:min(limit * 2, len(sorted_questions))]
    
    # Randomly select from top candidates
    if len(top_candidates) >= limit:
        selected = random.sample(top_candidates, limit)
    else:
        selected = top_candidates
    
    logger.info(f"[QUESTIONS] 🔄 Fallback mode: Selected {len(selected)} from {len(default_questions)} fallback questions")
    logger.debug(f"[QUESTIONS] Fallback questions selected:")
    for i, q in enumerate(selected, 1):
        logger.debug(f"  {i}. [{q.priority}] {q.question_text[:60]}...")
    
    return selected

