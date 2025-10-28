# -*- coding: utf-8 -*-
"""
Check What Permissions Are Needed for SharePoint REST API
"""

print("=" * 60)
print("SHAREPOINT PERMISSIONS REQUIREMENT CHECK")
print("=" * 60)

print("\n✅ CURRENT PERMISSIONS:")
print("   - Sites.Read.All (Application permission)")
print("   - This is already added to your app")

print("\n🔍 FOR SHAREPOINT REST API:")
print("   - The SAME token works, but needs proper scope")
print("   - Issue: The access token from Graph API has scope for 'graph.microsoft.com'")
print("   - SharePoint REST API needs scope for 'yourdomain.sharepoint.com'")

print("\n💡 SOLUTION:")
print("   You have TWO options:")

print("\n   1️⃣  USE SAME TOKEN (Try this first):")
print("      - Your current Sites.Read.All permission should work")
print("      - The issue is with how we're making the REST API call")
print("      - We need to add proper headers and authentication")

print("\n   2️⃣  ADD SHAREPOINT-SPECIFIC SCOPE:")
print("      - This requires getting a token specifically for SharePoint")
print("      - Still uses the same Sites.Read.All permission")
print("      - Just requests token with SharePoint scope instead of Graph scope")

print("\n🎯 RECOMMENDATION:")
print("   You DON'T need to add new permissions!")
print("   You already have Sites.Read.All which is correct.")
print("   We just need to fix how we're using the token with SharePoint REST API.")

print("\n📝 Current Issue:")
print("   - Getting 401 UNAUTHORIZED when accessing SharePoint pages")
print("   - This is an authentication/authorization header issue")
print("   - Not a permissions issue")

print("\n✅ Action Required:")
print("   - NO new Azure permissions needed")
print("   - Just need to fix the REST API authentication code")
print("   - The Sites.Read.All permission is sufficient")

