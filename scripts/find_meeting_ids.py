import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.sharepoint_auth import sharepoint_auth
import requests

print("=" * 60)
print("FINDING TEAMS MEETING IDs")
print("=" * 60)

headers = sharepoint_auth.get_headers()
user_email = os.getenv('TEAMS_TRANSCRIPT_USER_EMAILS', '').split(',')[0].strip()

if not user_email:
    print("Error: No user email configured")
    sys.exit(1)

print(f"Checking meetings for: {user_email}\n")

# Try different API endpoints to find meetings
endpoints = [
    f"https://graph.microsoft.com/v1.0/users/{user_email}/onlineMeetings",
    f"https://graph.microsoft.com/beta/users/{user_email}/onlineMeetings",
    f"https://graph.microsoft.com/v1.0/users/{user_email}/calendar/events?$top=10",
]

for endpoint in endpoints:
    print(f"[*] Trying: {endpoint}")
    try:
        resp = requests.get(endpoint, headers=headers, timeout=30)
        print(f"    Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('value', [])
            print(f"    Found {len(items)} items")
            
            if items:
                print("\n    Recent items:")
                for item in items[:3]:
                    print(f"    - {item.get('subject', item.get('name', 'Unknown'))}")
                    if 'id' in item:
                        print(f"      ID: {item['id']}")
                    if 'onlineMeeting' in item:
                        print(f"      Has online meeting: {item['onlineMeeting']}")
                print()
        else:
            print(f"    Error: {resp.text[:200]}")
    except Exception as e:
        print(f"    Exception: {e}")
    print()

print("=" * 60)
print("If you see meeting IDs above, we can use them to fetch transcripts!")


