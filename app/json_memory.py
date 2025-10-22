from typing import List, Dict, Optional
import asyncio
import json
import os
from datetime import datetime
import logging
from config import JSON_MEMORY_FILE

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONMemoryManager:
    """JSON file-based chat history management."""
    
    def __init__(self, data_file: str = JSON_MEMORY_FILE):
        self.data_file = data_file
        self._data_lock = asyncio.Lock()
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists."""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    async def _load_data(self) -> Dict:
        """Load data from JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading data from {self.data_file}: {e}")
            return {}
    
    async def _save_data(self, data: Dict):
        """Save data to JSON file."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving data to {self.data_file}: {e}")
    
    async def get_or_create_user_conversation(self, user_id: str) -> List[Dict[str, str]]:
        """Get or create a conversation for a specific user."""
        async with self._data_lock:
            data = await self._load_data()
            
            if user_id not in data:
                # Create new conversation
                data[user_id] = {
                    "messages": [],
                    "created_at": datetime.utcnow().isoformat(),
                    "last_updated": datetime.utcnow().isoformat()
                }
                await self._save_data(data)
                return []
            
            return data[user_id].get("messages", [])
    
    async def add_to_conversation(self, user_id: str, role: str, content: str):
        """Add a message to the user's conversation history."""
        async with self._data_lock:
            data = await self._load_data()
            
            # Get current conversation
            if user_id not in data:
                data[user_id] = {
                    "messages": [],
                    "created_at": datetime.utcnow().isoformat(),
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            # Add new message
            new_message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            data[user_id]["messages"].append(new_message)
            
            # Keep only last 20 messages to prevent context overflow
            if len(data[user_id]["messages"]) > 20:
                data[user_id]["messages"] = data[user_id]["messages"][-20:]
            
            # Update timestamp
            data[user_id]["last_updated"] = datetime.utcnow().isoformat()
            
            await self._save_data(data)
    
    async def get_conversation_context(self, user_id: str) -> str:
        """Get formatted conversation context for a user."""
        conversation = await self.get_or_create_user_conversation(user_id)
        
        if not conversation:
            return ""
        
        context = "\n\nPrevious conversation:\n"
        # Get last 5 messages for context
        for msg in conversation[-5:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"
        
        return context
    
    async def get_user_chat_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get full chat history for a user."""
        return await self.get_or_create_user_conversation(user_id)
    
    async def clear_user_chat_history(self, user_id: str):
        """Clear chat history for a specific user."""
        async with self._data_lock:
            data = await self._load_data()
            
            if user_id in data:
                data[user_id]["messages"] = []
                data[user_id]["last_updated"] = datetime.utcnow().isoformat()
                await self._save_data(data)
                logger.info(f"Cleared chat history for user {user_id}")
    
    async def get_all_users(self) -> List[str]:
        """Get list of all user IDs in the database."""
        data = await self._load_data()
        return list(data.keys())
    
    async def get_conversation_stats(self) -> Dict:
        """Get statistics about conversations."""
        data = await self._load_data()
        
        total_users = len(data)
        total_messages = sum(len(user_data.get("messages", [])) for user_data in data.values())
        
        return {
            "total_users": total_users,
            "total_messages": total_messages,
            "storage_type": "JSON",
            "data_file": self.data_file
        }
    
    async def connect(self):
        """Initialize JSON storage (no-op for file-based storage)."""
        logger.info(f"JSON memory storage initialized: {self.data_file}")
    
    async def disconnect(self):
        """Close JSON storage (no-op for file-based storage)."""
        logger.info("JSON memory storage closed")

# Global instance
json_memory = JSONMemoryManager()

# Async wrapper functions to maintain compatibility with existing code
async def get_or_create_user_conversation(user_id: str) -> List[Dict[str, str]]:
    """Get or create a conversation for a specific user."""
    return await json_memory.get_or_create_user_conversation(user_id)

async def add_to_conversation(user_id: str, role: str, content: str):
    """Add a message to the user's conversation history."""
    await json_memory.add_to_conversation(user_id, role, content)

async def get_conversation_context(user_id: str) -> str:
    """Get formatted conversation context for a user."""
    return await json_memory.get_conversation_context(user_id)

async def get_user_chat_history(user_id: str) -> List[Dict[str, str]]:
    """Get full chat history for a user."""
    return await json_memory.get_user_chat_history(user_id)

async def clear_user_chat_history(user_id: str):
    """Clear chat history for a specific user."""
    await json_memory.clear_user_chat_history(user_id)

# Additional utility functions
async def get_all_users() -> List[str]:
    """Get list of all user IDs in the database."""
    return await json_memory.get_all_users()

async def get_conversation_stats() -> Dict:
    """Get statistics about conversations."""
    return await json_memory.get_conversation_stats()

async def close_mongodb_connection():
    """Close JSON storage connection (maintains compatibility)."""
    await json_memory.disconnect()
