"""
Backup script for vectorstore and metadata.
Creates timestamped backup of ChromaDB and metadata before rebuilding.
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path

CHROMA_DB_PATH = "./data/chroma_db"
METADATA_FILE = "./data/vectorstore_metadata.json"
BACKUP_DIR = "./data/backups"


def create_backup():
    """Create timestamped backup of vectorstore and metadata."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"chroma_db_backup_{timestamp}")
    
    print("=" * 70)
    print("VECTORSTORE BACKUP")
    print("=" * 70)
    print(f"Timestamp: {timestamp}")
    print(f"Source: {CHROMA_DB_PATH}")
    print(f"Destination: {backup_path}")
    print()
    
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Check if vectorstore exists
    if not os.path.exists(CHROMA_DB_PATH):
        print("[WARNING] No existing vectorstore found to backup")
        print(f"[INFO] {CHROMA_DB_PATH} does not exist")
        return None
    
    try:
        # Backup ChromaDB
        print("[*] Backing up ChromaDB...")
        shutil.copytree(CHROMA_DB_PATH, backup_path)
        
        # Calculate backup size
        backup_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(backup_path)
            for filename in filenames
        )
        backup_size_mb = backup_size / (1024 * 1024)
        
        print(f"[OK] ChromaDB backed up successfully")
        print(f"[OK] Backup size: {backup_size_mb:.2f} MB")
        
        # Backup metadata if exists
        if os.path.exists(METADATA_FILE):
            print("[*] Backing up metadata...")
            metadata_backup = os.path.join(BACKUP_DIR, f"vectorstore_metadata_{timestamp}.json")
            shutil.copy2(METADATA_FILE, metadata_backup)
            print(f"[OK] Metadata backed up to: {metadata_backup}")
        
        # Get statistics from backup
        stats = get_backup_stats(backup_path)
        
        # Save backup log
        backup_log = {
            "timestamp": timestamp,
            "backup_path": backup_path,
            "source_path": CHROMA_DB_PATH,
            "backup_size_mb": backup_size_mb,
            "stats": stats
        }
        
        log_file = os.path.join(BACKUP_DIR, f"backup_log_{timestamp}.json")
        with open(log_file, 'w') as f:
            json.dump(backup_log, f, indent=2)
        
        print()
        print("=" * 70)
        print("BACKUP STATISTICS")
        print("=" * 70)
        print(f"Total files: {stats.get('total_files', 0)}")
        print(f"Backup size: {backup_size_mb:.2f} MB")
        print(f"Backup location: {backup_path}")
        print(f"Log file: {log_file}")
        print("=" * 70)
        print("[OK] Backup completed successfully!")
        print()
        
        return backup_path
        
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_backup_stats(backup_path):
    """Get statistics from backed up vectorstore."""
    stats = {
        "total_files": 0,
        "file_types": {}
    }
    
    try:
        for dirpath, _, filenames in os.walk(backup_path):
            for filename in filenames:
                stats["total_files"] += 1
                ext = os.path.splitext(filename)[1]
                stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
    except Exception as e:
        print(f"[WARNING] Could not get stats: {e}")
    
    return stats


def list_backups():
    """List all available backups."""
    if not os.path.exists(BACKUP_DIR):
        print("[INFO] No backups found")
        return []
    
    backups = []
    for item in os.listdir(BACKUP_DIR):
        item_path = os.path.join(BACKUP_DIR, item)
        if os.path.isdir(item_path) and item.startswith("chroma_db_backup_"):
            # Get backup info
            backup_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(item_path)
                for filename in filenames
            ) / (1024 * 1024)
            
            timestamp_str = item.replace("chroma_db_backup_", "")
            backups.append({
                "name": item,
                "path": item_path,
                "timestamp": timestamp_str,
                "size_mb": backup_size
            })
    
    backups.sort(key=lambda x: x["timestamp"], reverse=True)
    
    if backups:
        print("\nAvailable Backups:")
        print("-" * 70)
        for backup in backups:
            print(f"  {backup['timestamp']} - {backup['size_mb']:.2f} MB")
        print("-" * 70)
    
    return backups


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_backups()
    else:
        create_backup()

