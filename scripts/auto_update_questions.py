"""
Auto-Update Suggested Questions (Scheduled Task)

This script automatically updates suggested questions from user chat history.
Run this periodically (e.g., daily or weekly) to keep questions fresh.

Usage:
    # Run once
    python -m scripts.auto_update_questions
    
    # Or schedule it (Windows Task Scheduler / Linux cron)
    # Daily at 2 AM: python -m scripts.auto_update_questions
"""

import sys
import os
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.analyze_user_questions import analyze_user_questions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/question_updates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def auto_update():
    """
    Automatically update suggested questions from user history
    
    Default settings:
    - Analyze last 30 days
    - Minimum 2 occurrences
    - Add top 15 questions
    """
    try:
        logger.info("="*70)
        logger.info("AUTO-UPDATE SUGGESTED QUESTIONS STARTED")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)
        
        # Run analysis
        analyze_user_questions(
            days_back=30,      # Last 30 days
            min_frequency=2,   # Asked at least 2 times
            limit=15           # Top 15 questions
        )
        
        logger.info("="*70)
        logger.info("AUTO-UPDATE COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"Auto-update failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    auto_update()

