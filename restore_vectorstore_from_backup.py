#!/usr/bin/env python3
"""
Restore vectorstore from backup.

This script restores the vectorstore from the most recent backup.
"""

import os
import shutil
from datetime import datetime

CHROMA_DB_PATH = "./data/chroma_db"
BACKUP_PATH = "./data/chroma_db_backup_manual_20251111_172609"

def restore_from_backup():
    """Restore vectorstore from backup."""
    print("=" * 60)
    print("RESTORE VECTORSTORE FROM BACKUP")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check if backup exists
    if not os.path.exists(BACKUP_PATH):
        print(f"❌ ERROR: Backup not found at {BACKUP_PATH}")
        return False
    
    print(f"✓ Backup found: {BACKUP_PATH}")
    
    # Remove corrupted vectorstore
    if os.path.exists(CHROMA_DB_PATH):
        try:
            print(f"[*] Removing corrupted vectorstore...")
            shutil.rmtree(CHROMA_DB_PATH)
            print(f"✓ Removed corrupted vectorstore")
        except Exception as e:
            print(f"❌ Error removing corrupted vectorstore: {e}")
            return False
    
    # Restore from backup
    try:
        print(f"[*] Restoring from backup...")
        shutil.copytree(BACKUP_PATH, CHROMA_DB_PATH)
        print(f"✓ Successfully restored vectorstore from backup")
        return True
    except Exception as e:
        print(f"❌ Error restoring from backup: {e}")
        return False

if __name__ == "__main__":
    success = restore_from_backup()
    if success:
        print("\n" + "=" * 60)
        print("✅ RESTORE COMPLETE")
        print("=" * 60)
        print("You can now run: python test_query_context_relevance.py")
    else:
        print("\n" + "=" * 60)
        print("❌ RESTORE FAILED")
        print("=" * 60)

