# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.endpoints import router as chat_router
from app.routes.suggested_questions import router as questions_router
from app.mongodb_memory import close_mongodb_connection
import uvicorn
import asyncio
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    from app.mongodb_memory import mongodb_memory
    try:
        await mongodb_memory.connect()
        print("[OK] MongoDB memory storage initialized successfully")
        
        # Auto-seed suggested questions if database is empty
        await auto_seed_questions()
    except Exception as e:
        print(f"[ERROR] Failed to initialize MongoDB memory storage: {e}")
    
    yield
    
    # Shutdown
    try:
        await close_mongodb_connection()
        print("[OK] MongoDB memory storage closed")
    except Exception as e:
        print(f"[WARNING] Error closing MongoDB memory storage: {e}")


async def auto_seed_questions():
    """Automatically seed suggested questions if database is empty"""
    try:
        from app.mongodb_memory import mongodb_memory
        from datetime import datetime
        
        if mongodb_memory.database is None:
            print("[SEED] Skipping auto-seed: database not connected")
            return
        
        db = mongodb_memory.database
        collection = db.suggested_questions
        
        # Check if questions already exist
        existing_count = await collection.count_documents({})
        
        if existing_count > 0:
            print(f"[SEED] Suggested questions already seeded ({existing_count} questions found)")
            return
        
        print("[SEED] No suggested questions found. Auto-seeding...")
        
        # Import seed data from the seed script
        from scripts.seed_suggested_questions import INITIAL_QUESTIONS
        
        seeded_count = 0
        for q_data in INITIAL_QUESTIONS:
            question_doc = {
                **q_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "display_count": 0,
                "click_count": 0,
                "click_rate": 0.0,
                "target_user_roles": [],
                "created_by": "system_auto_seed"
            }
            await collection.insert_one(question_doc)
            seeded_count += 1
        
        print(f"[SEED] ✅ Successfully seeded {seeded_count} suggested questions")
        
    except Exception as e:
        print(f"[SEED] ⚠️  Warning: Failed to auto-seed questions: {e}")
        print("[SEED] Application will continue with default fallback questions")

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Enable credentials for OAuth
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Add a simple health check endpoint
@app.get("/")
async def root():
    return {"message": "CF Chatbot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Server is running"}

app.include_router(chat_router)
app.include_router(questions_router)

# Mount static directories for images and other assets
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/data", StaticFiles(directory="data"), name="data")

# Serve HTML files
@app.get("/login.html")
async def serve_login():
    return FileResponse("login.html")

@app.get("/index.html")
async def serve_index():
    return FileResponse("index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)