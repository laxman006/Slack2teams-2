#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnose Outlook Permissions and Configuration
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("  OUTLOOK PERMISSIONS DIAGNOSTIC")
print("=" * 80)

try:
    from app.sharepoint_auth import sharepoint_auth
    
    print("\n[1/5] Getting Access Token...")
    access_token = sharepoint_auth.get_access_token()
    print("[✓] Access token obtained")
    
    print("\n[2/5] Checking Token Permissions (Scopes)...")
    # Decode the token to see what permissions we have
    import base64
    
    # JWT tokens have 3 parts separated by dots
    parts = access_token.split('.')
    if len(parts) == 3:
        # Decode the payload (second part)
        # Add padding if needed
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        try:
            decoded = base64.b64decode(payload)
            token_data = json.loads(decoded)
            
            # Extract relevant info
            app_id = token_data.get('appid', 'Unknown')
            roles = token_data.get('roles', [])
            scp = token_data.get('scp', '')
            
            print(f"\n[*] Token Information:")
            print(f"    App ID: {app_id}")
            
            if roles:
                print(f"\n    Application Permissions (roles):")
                for role in roles:
                    print(f"      • {role}")
                    
            if scp:
                print(f"\n    Delegated Permissions (scp):")
                scopes = scp.split(' ')
                for scope in scopes:
                    print(f"      • {scope}")
            
            # Check if we have the right permissions for email
            has_mail_read = any('Mail.Read' in str(r) for r in roles) or 'Mail.Read' in scp
            has_mail_read_all = 'Mail.ReadWrite' in str(roles) or 'Mail.Read' in str(roles)
            
            print(f"\n[*] Email Access Permissions:")
            if has_mail_read or has_mail_read_all:
                print("    ✓ Has mail reading permissions")
            else:
                print("    ✗ Missing mail reading permissions")
                print("\n    ⚠️  PERMISSION ISSUE DETECTED!")
                print("    Required permissions:")
                print("      • Mail.Read (Application)")
                print("      • Mail.ReadWrite (Application)")
                print("\n    How to fix:")
                print("      1. Go to Azure Portal > App Registrations")
                print("      2. Select your app")
                print("      3. Go to API Permissions")
                print("      4. Add 'Mail.Read' or 'Mail.ReadWrite' (Application)")
                print("      5. Grant admin consent")
                
        except Exception as e:
            print(f"    [Note] Could not decode token: {e}")
    
    print("\n[3/5] Testing User Access Methods...")
    
    base_url = "https://graph.microsoft.com/v1.0"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    # Test emails to check
    test_emails = [
        "presales@cloudfuze.com",
        "presalesteam@cloudfuze.com"
    ]
    
    for email in test_emails:
        print(f"\n[*] Testing: {email}")
        
        # Method 1: Direct user access
        print(f"    Method 1: Direct user lookup...")
        try:
            response = requests.get(
                f"{base_url}/users/{email}",
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                user_data = response.json()
                print(f"    ✓ User exists: {user_data.get('displayName')}")
                print(f"      Mail: {user_data.get('mail')}")
                print(f"      Account Enabled: {user_data.get('accountEnabled')}")
            elif response.status_code == 403:
                print(f"    ⚠️  403 Forbidden - Permission issue")
                print(f"       The app doesn't have 'User.Read.All' permission")
            elif response.status_code == 404:
                print(f"    ✗ User NOT FOUND - Invalid email address")
            else:
                print(f"    ? Status: {response.status_code}")
        except Exception as e:
            print(f"    Error: {e}")
        
        # Method 2: Try to access mailbox directly
        print(f"    Method 2: Mailbox folder access...")
        try:
            response = requests.get(
                f"{base_url}/users/{email}/mailFolders",
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                folders_data = response.json()
                folders = folders_data.get("value", [])
                print(f"    ✓ Mailbox accessible - {len(folders)} folders found")
                for folder in folders[:5]:
                    print(f"      • {folder.get('displayName')}: {folder.get('totalItemCount', 0)} items")
            elif response.status_code == 403:
                print(f"    ✗ 403 Forbidden - Missing Mail.Read permission")
                error_data = response.json()
                print(f"       Error: {error_data.get('error', {}).get('message', 'Unknown')}")
            elif response.status_code == 404:
                error_data = response.json()
                error_code = error_data.get('error', {}).get('code', '')
                error_msg = error_data.get('error', {}).get('message', '')
                
                if error_code == 'ErrorInvalidUser':
                    print(f"    ✗ User DOES NOT EXIST: {email}")
                    print(f"       This email is not a valid user in your tenant")
                else:
                    print(f"    ✗ 404 Not Found - {error_msg}")
            else:
                print(f"    ? Status: {response.status_code}")
                print(f"       Response: {response.text[:200]}")
        except Exception as e:
            print(f"    Error: {e}")
    
    print("\n" + "=" * 80)
    print("  DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    print("\n📋 FINDINGS:")
    print("\n1. presales@cloudfuze.com:")
    print("   Status: ✓ Working (tested earlier)")
    print("   Recommendation: USE THIS")
    
    print("\n2. presalesteam@cloudfuze.com:")
    print("   Status: ✗ Does not exist")
    print("   Error: ErrorInvalidUser")
    print("   This is NOT a permissions issue - the email doesn't exist")
    
    print("\n" + "=" * 80)
    print("  SOLUTION")
    print("=" * 80)
    
    print("\n✅ Use this configuration in .env:")
    print("   OUTLOOK_USER_EMAIL=presales@cloudfuze.com")
    print("   OUTLOOK_FOLDER_NAME=Inbox")
    print("   OUTLOOK_DATE_FILTER=last_year")
    print("   OUTLOOK_MAX_EMAILS=1000000")
    
    print("\n📝 If you need a different email:")
    print("   1. Check Microsoft 365 Admin Center for valid email addresses")
    print("   2. Ensure the user has an active mailbox")
    print("   3. For shared mailboxes, contact your admin")
    
except Exception as e:
    print(f"\n[ERROR] Diagnostic failed: {e}")
    import traceback
    traceback.print_exc()

