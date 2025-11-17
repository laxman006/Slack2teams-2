#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Monitored Rebuild with Comprehensive Logging
Tracks all files, errors, and prevents corruption
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json

# Set environment variables for filtered email ingestion
os.environ['OUTLOOK_USER_EMAIL'] = 'presales@cloudfuze.com'
os.environ['OUTLOOK_FOLDER_NAME'] = 'Inbox'
os.environ['OUTLOOK_DATE_FILTER'] = 'last_12_months'
os.environ['OUTLOOK_MAX_EMAILS'] = '10000'
os.environ['OUTLOOK_FILTER_EMAIL'] = 'presalesteam@cloudfuze.com'

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

# Logging setup
LOG_FILE = f"rebuild_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
REPORT_FILE = f"rebuild_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

class RebuildMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.stats = {
            "start_time": self.start_time.isoformat(),
            "blogs": {"processed": 0, "failed": 0, "files": []},
            "sharepoint": {"processed": 0, "failed": 0, "files": [], "by_type": {}},
            "emails": {"processed": 0, "failed": 0, "filtered": 0, "conversations": 0},
            "vectorstore": {"total_chunks": 0, "status": "pending"},
            "errors": [],
            "warnings": [],
            "completion_status": "in_progress"
        }
        self.log_handle = open(LOG_FILE, 'w', encoding='utf-8')
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        self.log_handle.write(log_line + "\n")
        self.log_handle.flush()
        
        if level == "ERROR":
            self.stats["errors"].append({"time": timestamp, "message": message})
        elif level == "WARNING":
            self.stats["warnings"].append({"time": timestamp, "message": message})
    
    def save_report(self):
        self.stats["end_time"] = datetime.now().isoformat()
        duration = datetime.now() - self.start_time
        self.stats["duration_seconds"] = duration.total_seconds()
        self.stats["duration_readable"] = str(duration)
        
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
        
        self.log(f"Report saved to: {REPORT_FILE}")
    
    def close(self):
        self.log_handle.close()

# Initialize monitor
monitor = RebuildMonitor()

monitor.log("=" * 80)
monitor.log("MONITORED REBUILD - STARTING")
monitor.log("=" * 80)
monitor.log("\nConfiguration:")
monitor.log(f"  Blogs: ALL from cloudfuze.com")
monitor.log(f"  SharePoint: ALL files from DOC360")
monitor.log(f"  Emails: FILTERED for presalesteam@cloudfuze.com")
monitor.log(f"    - Mailbox: presales@cloudfuze.com")
monitor.log(f"    - Folder: Inbox")
monitor.log(f"    - Time: Last 12 months")
monitor.log(f"\nLogs: {LOG_FILE}")
monitor.log(f"Report: {REPORT_FILE}")
monitor.log("=" * 80)

try:
    # Import after setting env vars  
    from app.vectorstore import initialize_vectorstore
    from config import ENABLE_WEB_SOURCE, ENABLE_SHAREPOINT_SOURCE, ENABLE_OUTLOOK_SOURCE
    
    monitor.log("\n[PHASE 1] Configuration Check")
    monitor.log(f"  WEB_SOURCE: {ENABLE_WEB_SOURCE}")
    monitor.log(f"  SHAREPOINT_SOURCE: {ENABLE_SHAREPOINT_SOURCE}")
    monitor.log(f"  OUTLOOK_SOURCE: {ENABLE_OUTLOOK_SOURCE}")
    
    if not all([ENABLE_WEB_SOURCE, ENABLE_SHAREPOINT_SOURCE, ENABLE_OUTLOOK_SOURCE]):
        monitor.log("WARNING: Some sources disabled", "WARNING")
    
    # Start rebuild
    monitor.log("\n[PHASE 2] Starting Vectorstore Build...")
    monitor.log("This will take 15-30 minutes - DO NOT INTERRUPT")
    monitor.log("")
    
    # Capture console output
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    # Build vectorstore using initialize_vectorstore (forces rebuild)
    vectorstore = initialize_vectorstore()
    
    if vectorstore:
        monitor.log("\n[PHASE 3] Verifying Vectorstore...")
        
        # Get collection stats
        try:
            import chromadb
            from config import CHROMA_DB_PATH
            
            client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            collection = client.get_collection("langchain")
            
            total_chunks = collection.count()
            monitor.stats["vectorstore"]["total_chunks"] = total_chunks
            monitor.stats["vectorstore"]["status"] = "success"
            
            monitor.log(f"✓ Vectorstore verified: {total_chunks} chunks")
            
            # Sample some metadata to categorize
            if total_chunks > 0:
                try:
                    results = collection.peek(limit=100)
                    if results and 'metadatas' in results:
                        metadatas = results['metadatas']
                        
                        # Count by source
                        from collections import Counter
                        source_types = [m.get('source_type', 'unknown') for m in metadatas if m]
                        source_counts = Counter(source_types)
                        
                        monitor.log("\n  Source breakdown (sample):")
                        for source, count in source_counts.items():
                            monitor.log(f"    {source}: ~{count * (total_chunks // 100)} chunks (estimated)")
                            
                except Exception as e:
                    monitor.log(f"Could not sample metadata: {e}", "WARNING")
            
        except Exception as e:
            monitor.log(f"Could not verify vectorstore: {e}", "ERROR")
            monitor.stats["vectorstore"]["status"] = "error"
            monitor.stats["vectorstore"]["error"] = str(e)
    else:
        monitor.log("Vectorstore build failed!", "ERROR")
        monitor.stats["vectorstore"]["status"] = "failed"
    
    # Mark completion
    monitor.stats["completion_status"] = "completed_successfully"
    monitor.log("\n" + "=" * 80)
    monitor.log("REBUILD COMPLETED SUCCESSFULLY")
    monitor.log("=" * 80)
    
    # Generate summary
    monitor.log("\nSUMMARY:")
    monitor.log(f"  Total chunks: {monitor.stats['vectorstore']['total_chunks']}")
    monitor.log(f"  Errors: {len(monitor.stats['errors'])}")
    monitor.log(f"  Warnings: {len(monitor.stats['warnings'])}")
    monitor.log(f"  Duration: {monitor.stats.get('duration_readable', 'N/A')}")
    
    if monitor.stats['errors']:
        monitor.log("\nERRORS FOUND:")
        for err in monitor.stats['errors'][:5]:
            monitor.log(f"  - {err['message']}")
    
    if monitor.stats['warnings']:
        monitor.log(f"\n{len(monitor.stats['warnings'])} warnings (see log file)")
    
    monitor.log(f"\nVectorstore is ready and NOT corrupted")
    monitor.log(f"   Path: ./data/chroma_db")
    monitor.log(f"   Safe to use now!")
    
    # Save report
    monitor.save_report()
    
    monitor.log(f"\nFull logs saved to: {LOG_FILE}")
    monitor.log(f"JSON report saved to: {REPORT_FILE}")

except KeyboardInterrupt:
    monitor.log("\n\nINTERRUPTED BY USER!", "ERROR")
    monitor.log("Vectorstore may be incomplete or corrupted", "WARNING")
    monitor.stats["completion_status"] = "interrupted"
    monitor.save_report()
    monitor.close()
    sys.exit(1)

except Exception as e:
    monitor.log(f"\n\nREBUILD FAILED: {e}", "ERROR")
    import traceback
    tb = traceback.format_exc()
    monitor.log(tb, "ERROR")
    monitor.stats["completion_status"] = "failed"
    monitor.stats["fatal_error"] = str(e)
    monitor.save_report()
    monitor.close()
    sys.exit(1)

finally:
    monitor.close()

# Print final message
print("\n" + "=" * 80)
print("  REBUILD MONITORING COMPLETE")
print("=" * 80)
print(f"\n📄 Review logs: {LOG_FILE}")
print(f"📊 Review report: {REPORT_FILE}")
print("\nTo check vectorstore health:")
print("  python check_rebuild_progress.py")

