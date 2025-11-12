# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.endpoints import router as chat_router
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
    except Exception as e:
        print(f"[ERROR] Failed to initialize MongoDB memory storage: {e}")
    
    yield
    
    # Shutdown
    try:
        await close_mongodb_connection()
        print("[OK] MongoDB memory storage closed")
    except Exception as e:
        print(f"[WARNING] Error closing MongoDB memory storage: {e}")

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Enable credentials for OAuth
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Health check endpoints
@app.get("/")
async def root():
    return {"message": "CF Chatbot API is running"}

@app.get("/health")
async def health_check():
    """Basic health check - always returns 200 if server is up."""
    return {"status": "healthy", "message": "Server is running"}

@app.get("/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are ready.
    Returns 200 if ready, 503 if not ready.
    """
    from fastapi import status
    from fastapi.responses import JSONResponse
    
    health_status = {
        "ready": True,
        "checks": {}
    }
    
    # Check MongoDB connectivity
    try:
        from app.mongodb_memory import mongodb_memory
        await mongodb_memory.connect()
        health_status["checks"]["mongodb"] = "connected"
    except Exception as e:
        health_status["ready"] = False
        health_status["checks"]["mongodb"] = f"error: {str(e)}"
    
    # Check vectorstore availability
    try:
        from app.vectorstore import vectorstore
        if vectorstore:
            health_status["checks"]["vectorstore"] = "available"
        else:
            health_status["ready"] = False
            health_status["checks"]["vectorstore"] = "not initialized"
    except Exception as e:
        health_status["ready"] = False
        health_status["checks"]["vectorstore"] = f"error: {str(e)}"
    
    # Check Langfuse connectivity
    try:
        from app.langfuse_integration import langfuse_tracker
        if langfuse_tracker and langfuse_tracker.client:
            health_status["checks"]["langfuse"] = "connected"
        else:
            # Langfuse is optional, so mark as warning not failure
            health_status["checks"]["langfuse"] = "not configured"
    except Exception as e:
        health_status["checks"]["langfuse"] = f"warning: {str(e)}"
    
    if health_status["ready"]:
        return JSONResponse(content=health_status, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content=health_status, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

app.include_router(chat_router)

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