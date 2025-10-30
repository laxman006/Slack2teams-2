"""
MongoDB Data Manager
Centralized access to all data stored in MongoDB.
Replaces local file access with MongoDB queries.
"""

from pymongo import MongoClient
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import MONGODB_URL, MONGODB_DATABASE


class MongoDBDataManager:
    """Manages all data access to MongoDB."""
    
    def __init__(self):
        """Initialize MongoDB connection."""
        self.client = MongoClient(MONGODB_URL)
        self.db = self.client[MONGODB_DATABASE]
    
    # ==================== FINE-TUNING DATA ====================
    
    def get_corrections(self) -> List[Dict[str, Any]]:
        """Get all fine-tuning corrections."""
        return list(self.db["fine_tuning_data"].find({"type": "correction"}))
    
    def add_correction(self, correction: Dict[str, Any]):
        """Add a new correction for fine-tuning."""
        correction["type"] = "correction"
        correction["created_at"] = datetime.utcnow()
        self.db["fine_tuning_data"].insert_one(correction)
    
    def get_training_data(self, source_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get training data, optionally filtered by source file."""
        query = {"type": "training_data"}
        if source_file:
            query["source_file"] = source_file
        return list(self.db["fine_tuning_data"].find(query))
    
    def get_fine_tuning_status(self) -> Optional[Dict[str, Any]]:
        """Get current fine-tuning job status."""
        return self.db["fine_tuning_status"].find_one()
    
    def update_fine_tuning_status(self, status: Dict[str, Any]):
        """Update fine-tuning job status."""
        status["updated_at"] = datetime.utcnow()
        self.db["fine_tuning_status"].replace_one(
            {"job_id": status.get("job_id", "current")},
            status,
            upsert=True
        )
    
    # ==================== FEEDBACK ====================
    
    def get_feedback(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get feedback, optionally filtered by user."""
        query = {"user_id": user_id} if user_id else {}
        return list(self.db["feedback_history"].find(query))
    
    def add_feedback(self, feedback: Dict[str, Any]):
        """Add user feedback."""
        feedback["created_at"] = datetime.utcnow()
        self.db["feedback_history"].insert_one(feedback)
    
    def get_feedback_stats(self) -> Dict[str, int]:
        """Get feedback statistics."""
        total = self.db["feedback_history"].count_documents({})
        positive = self.db["feedback_history"].count_documents({"rating": "positive"})
        negative = self.db["feedback_history"].count_documents({"rating": "negative"})
        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "positive_rate": (positive / total * 100) if total > 0 else 0
        }
    
    # ==================== CORRECTED RESPONSES ====================
    
    def get_corrected_responses(self) -> List[Dict[str, Any]]:
        """Get all corrected responses."""
        return list(self.db["corrected_responses"].find({}))
    
    def add_corrected_response(self, key: str, response: Dict[str, Any]):
        """Add a corrected response."""
        response["key"] = key
        response["created_at"] = datetime.utcnow()
        self.db["corrected_responses"].replace_one(
            {"key": key},
            response,
            upsert=True
        )
    
    # ==================== BAD RESPONSES ====================
    
    def get_bad_responses(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get bad response traces."""
        return list(self.db["bad_responses"].find({}).sort("_id", -1).limit(limit))
    
    def add_bad_response(self, response: Dict[str, Any]):
        """Add a bad response trace."""
        response["created_at"] = datetime.utcnow()
        self.db["bad_responses"].insert_one(response)
    
    # ==================== VECTORSTORE METADATA ====================
    
    def get_vectorstore_metadata(self) -> Optional[Dict[str, Any]]:
        """Get vectorstore metadata."""
        return self.db["vectorstore_metadata"].find_one({"_id": "current"})
    
    def update_vectorstore_metadata(self, metadata: Dict[str, Any]):
        """Update vectorstore metadata."""
        metadata["updated_at"] = datetime.utcnow()
        self.db["vectorstore_metadata"].replace_one(
            {"_id": "current"},
            {**metadata, "_id": "current"},
            upsert=True
        )
    
    # ==================== STATISTICS ====================
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections."""
        return {
            "fine_tuning_corrections": self.db["fine_tuning_data"].count_documents({"type": "correction"}),
            "fine_tuning_training_data": self.db["fine_tuning_data"].count_documents({"type": "training_data"}),
            "feedback_items": self.db["feedback_history"].count_documents({}),
            "corrected_responses": self.db["corrected_responses"].count_documents({}),
            "bad_responses": self.db["bad_responses"].count_documents({}),
            "chat_histories": self.db["chat_histories"].count_documents({}),
            "vector_documents": self.db["cloudfuze_vectorstore"].count_documents({}),
        }
    
    def __del__(self):
        """Close MongoDB connection."""
        if hasattr(self, 'client'):
            self.client.close()


# Global instance for easy access
mongodb_data = MongoDBDataManager()


# ==================== HELPER FUNCTIONS ====================

def get_corrections_for_finetuning() -> List[Dict[str, Any]]:
    """Get corrections in OpenAI fine-tuning format."""
    corrections = mongodb_data.get_corrections()
    
    # Convert to OpenAI format if needed
    formatted = []
    for correction in corrections:
        if "messages" in correction:
            formatted.append({
                "messages": correction["messages"]
            })
    
    return formatted


def save_correction(user_query: str, bad_response: str, good_response: str, user_id: str = "unknown"):
    """Save a correction for fine-tuning."""
    correction = {
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": good_response}
        ],
        "metadata": {
            "user_id": user_id,
            "bad_response": bad_response,
            "corrected_at": datetime.utcnow().isoformat()
        }
    }
    mongodb_data.add_correction(correction)


def log_bad_response(query: str, response: str, error: str, user_id: str = "unknown"):
    """Log a bad response for debugging."""
    mongodb_data.add_bad_response({
        "query": query,
        "response": response,
        "error": error,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    })




