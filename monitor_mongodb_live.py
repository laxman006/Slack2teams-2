#!/usr/bin/env python3
"""
Real-time MongoDB monitoring to show where data is being saved.
Run this while testing your UI to see live updates.
"""

import time
from datetime import datetime
from pymongo import MongoClient
from config import MONGODB_URL, MONGODB_DATABASE

def clear_screen():
    """Clear terminal screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def get_collection_stats(db):
    """Get document counts and latest documents from all collections."""
    collections_to_monitor = [
        'feedback_history',
        'corrected_responses',
        'fine_tuning_data',
        'chat_histories',
        'cloudfuze_vectorstore',
        'bad_responses'
    ]
    
    stats = {}
    for coll_name in collections_to_monitor:
        coll = db[coll_name]
        count = coll.count_documents({})
        
        # Get latest document
        latest = coll.find_one(sort=[('_id', -1)])
        
        stats[coll_name] = {
            'count': count,
            'latest': latest
        }
    
    return stats

def format_timestamp(ts):
    """Format timestamp for display."""
    if not ts:
        return "N/A"
    if isinstance(ts, str):
        return ts
    if hasattr(ts, 'strftime'):
        return ts.strftime('%Y-%m-%d %H:%M:%S')
    return str(ts)

def display_stats(stats, previous_stats):
    """Display statistics with change indicators."""
    clear_screen()
    
    print("=" * 80)
    print("🔴 LIVE MONGODB MONITORING - Refresh every 2 seconds")
    print("=" * 80)
    print(f"⏰ Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Database: {MONGODB_DATABASE}")
    print("=" * 80)
    
    for coll_name, data in stats.items():
        count = data['count']
        latest = data['latest']
        
        # Check if count changed
        prev_count = previous_stats.get(coll_name, {}).get('count', 0)
        change_indicator = ""
        if count > prev_count:
            change_indicator = f" 🆕 (+{count - prev_count})"
        
        print(f"\n📁 Collection: {coll_name}")
        print(f"   📊 Total Documents: {count}{change_indicator}")
        
        if latest:
            # Show relevant fields based on collection
            if coll_name == 'feedback_history':
                print(f"   📝 Latest Feedback:")
                print(f"      • Trace ID: {latest.get('trace_id', 'N/A')}")
                print(f"      • Rating: {latest.get('rating', 'N/A')}")
                print(f"      • Comment: {latest.get('comment', 'None')}")
                print(f"      • Timestamp: {format_timestamp(latest.get('timestamp'))}")
                
            elif coll_name == 'corrected_responses':
                print(f"   ✏️ Latest Correction:")
                print(f"      • Trace ID: {latest.get('trace_id', 'N/A')}")
                response = latest.get('corrected_response', {})
                if isinstance(response, dict):
                    print(f"      • Messages: {len(response.get('messages', []))}")
                print(f"      • Created: {format_timestamp(latest.get('created_at'))}")
                
            elif coll_name == 'chat_histories':
                print(f"   💬 Latest Chat:")
                print(f"      • User ID: {latest.get('user_id', 'N/A')}")
                messages = latest.get('messages', [])
                print(f"      • Messages: {len(messages)}")
                print(f"      • Updated: {format_timestamp(latest.get('updated_at'))}")
                
            elif coll_name == 'fine_tuning_data':
                print(f"   🎓 Latest Training Data:")
                print(f"      • Type: {latest.get('type', 'N/A')}")
                print(f"      • Trace ID: {latest.get('trace_id', 'N/A')}")
                print(f"      • Created: {format_timestamp(latest.get('created_at'))}")
                
            elif coll_name == 'cloudfuze_vectorstore':
                print(f"   🔍 Vector Store:")
                print(f"      • Document: {latest.get('document', 'N/A')[:50]}...")
                metadata = latest.get('metadata', {})
                print(f"      • Source: {metadata.get('source', 'N/A')}")
                
    print("\n" + "=" * 80)
    print("💡 Testing Guide:")
    print("   1. Open browser: http://localhost:8000")
    print("   2. Ask a question → Watch 'chat_histories' increase")
    print("   3. Click 👍 or 👎 → Watch 'feedback_history' increase")
    print("   4. Submit correction → Watch 'corrected_responses' & 'fine_tuning_data'")
    print("=" * 80)
    print("Press Ctrl+C to stop monitoring")
    print("=" * 80)

def main():
    """Main monitoring loop."""
    print("Connecting to MongoDB...")
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    db = client[MONGODB_DATABASE]
    
    print("✅ Connected! Starting real-time monitoring...\n")
    time.sleep(2)
    
    previous_stats = {}
    
    try:
        while True:
            stats = get_collection_stats(db)
            display_stats(stats, previous_stats)
            previous_stats = stats
            time.sleep(2)  # Refresh every 2 seconds
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped.")
        client.close()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        client.close()

if __name__ == "__main__":
    main()




