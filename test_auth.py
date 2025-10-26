#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Microsoft OAuth Configuration Test Script
Tests environment variables, Azure AD connectivity, and backend health.
"""

import os
from dotenv import load_dotenv
import httpx
import asyncio
from datetime import datetime

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(status: bool, message: str):
    """Print a status message with color coding."""
    icon = f"{Colors.GREEN}✅{Colors.RESET}" if status else f"{Colors.RED}❌{Colors.RESET}"
    print(f"   {icon} {message}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"   {Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_info(message: str):
    """Print an info message."""
    print(f"   {Colors.BLUE}💡 {message}{Colors.RESET}")

def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{title}{Colors.RESET}")
    print("-" * 60)

async def test_microsoft_config():
    """Test Microsoft OAuth configuration."""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}Microsoft OAuth Configuration Test{Colors.RESET}")
    print(f"{Colors.BOLD}Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    print_section("1. Environment Variables")
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    tenant = os.getenv("MICROSOFT_TENANT")
    openai_key = os.getenv("OPENAI_API_KEY")
    langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
    mongodb_url = os.getenv("MONGODB_URL")
    
    print_status(bool(client_id), f"MICROSOFT_CLIENT_ID: {'Set (' + client_id[:8] + '...)' if client_id else 'Missing'}")
    print_status(bool(client_secret), f"MICROSOFT_CLIENT_SECRET: {'Set (***hidden***)' if client_secret else 'Missing'}")
    print_status(bool(tenant), f"MICROSOFT_TENANT: {tenant or 'Missing (using default: common)'}")
    print_status(bool(openai_key), f"OPENAI_API_KEY: {'Set (***hidden***)' if openai_key else 'Missing'}")
    print_status(bool(langfuse_public), f"LANGFUSE_PUBLIC_KEY: {'Set' if langfuse_public else 'Missing'}")
    print_status(bool(langfuse_secret), f"LANGFUSE_SECRET_KEY: {'Set' if langfuse_secret else 'Missing'}")
    print_status(bool(mongodb_url), f"MONGODB_URL: {mongodb_url or 'Using default: mongodb://localhost:27017'}")
    
    if not all([client_id, client_secret]):
        print(f"\n{Colors.RED}❌ Missing required Microsoft OAuth environment variables!{Colors.RESET}")
        print_info("Create a .env file with MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET")
        return False
    
    if not openai_key:
        print_warning("OPENAI_API_KEY is missing - chatbot will not work")
    
    # Test Azure AD endpoint
    print_section("2. Azure AD Connectivity")
    tenant_to_test = tenant or "common"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            url = f"https://login.microsoftonline.com/{tenant_to_test}/v2.0/.well-known/openid-configuration"
            print(f"   Testing: {url}")
            response = await http_client.get(url)
            
            if response.status_code == 200:
                print_status(True, f"Azure AD endpoint reachable (tenant: {tenant_to_test})")
                config = response.json()
                print_info(f"Authorization endpoint: {config.get('authorization_endpoint', 'N/A')}")
                print_info(f"Token endpoint: {config.get('token_endpoint', 'N/A')}")
            else:
                print_status(False, f"Azure AD endpoint returned {response.status_code}")
                print(f"      Response: {response.text[:200]}")
    except Exception as e:
        print_status(False, f"Cannot reach Azure AD: {str(e)}")
        print_warning("Check your internet connection or firewall settings")
    
    # Test backend connectivity
    print_section("3. Backend Connectivity")
    backend_urls = [
        "http://localhost:8002",
        "http://127.0.0.1:8002",
    ]
    
    backend_running = False
    for base_url in backend_urls:
        try:
            async with httpx.AsyncClient(timeout=5.0) as http_client:
                # Test health endpoint
                response = await http_client.get(f"{base_url}/health")
                if response.status_code == 200:
                    print_status(True, f"Backend is running at {base_url}")
                    backend_running = True
                    
                    # Test root endpoint
                    root_response = await http_client.get(base_url)
                    if root_response.status_code == 200:
                        print_info(f"Root endpoint: {root_response.json()}")
                    
                    # Test OAuth callback endpoint
                    test_payload = {
                        "code": "test_code",
                        "redirect_uri": "http://localhost:8002/index.html",
                        "code_verifier": "test_verifier"
                    }
                    oauth_response = await http_client.post(
                        f"{base_url}/auth/microsoft/callback",
                        json=test_payload
                    )
                    print_info(f"OAuth endpoint status: {oauth_response.status_code} (expected: 200 or error)")
                    
                    break
                else:
                    print_status(False, f"Backend at {base_url} returned {response.status_code}")
        except httpx.ConnectError:
            print_status(False, f"Backend not reachable at {base_url}")
        except Exception as e:
            print_status(False, f"Error testing {base_url}: {str(e)}")
    
    if not backend_running:
        print_warning("Backend is not running")
        print_info("Start backend with: python server.py")
        print_info("Or with reload: uvicorn server:app --host 0.0.0.0 --port 8002 --reload")
    
    # Test MongoDB connection
    print_section("4. MongoDB Connectivity")
    mongodb_url = mongodb_url or "mongodb://localhost:27017"
    
    try:
        # Try to import and test MongoDB
        from motor.motor_asyncio import AsyncIOMotorClient
        
        client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        print_status(True, f"MongoDB is reachable at {mongodb_url}")
        
        # List databases
        db_list = await client.list_database_names()
        print_info(f"Available databases: {', '.join(db_list[:5])}")
        
        client.close()
    except ImportError:
        print_warning("motor package not installed - cannot test MongoDB")
        print_info("Install with: pip install motor")
    except Exception as e:
        print_status(False, f"Cannot reach MongoDB: {str(e)}")
        print_warning("Make sure MongoDB is running")
        print_info("Start MongoDB or use MongoDB Atlas connection string")
    
    # Check login.html configuration
    print_section("5. Frontend Configuration")
    
    try:
        if os.path.exists("login.html"):
            with open("login.html", "r", encoding="utf-8") as f:
                content = f.read()
                
                # Check client ID in frontend
                if client_id and client_id in content:
                    print_status(True, "MICROSOFT_CLIENT_ID found in login.html")
                else:
                    print_status(False, "MICROSOFT_CLIENT_ID not found in login.html")
                    print_warning("Update MICROSOFT_CLIENT_ID in login.html line 148")
                
                # Check for tenant
                if tenant and tenant in content:
                    print_status(True, f"Tenant '{tenant}' found in login.html")
                elif 'MICROSOFT_TENANT = "cloudfuze.com"' in content:
                    print_status(True, "Tenant set to 'cloudfuze.com' in login.html")
                else:
                    print_warning("Tenant configuration might need updating in login.html")
                
                # Check if using sessionStorage or localStorage
                if "sessionStorage.setItem('code_verifier'" in content:
                    print_info("Using sessionStorage for code_verifier (may have issues)")
                    print_info("Consider switching to localStorage for better reliability")
                elif "localStorage.setItem('code_verifier'" in content:
                    print_status(True, "Using localStorage for code_verifier")
        else:
            print_status(False, "login.html not found")
    except Exception as e:
        print_warning(f"Error checking frontend config: {e}")
    
    # Check index.html configuration
    if os.path.exists("index.html"):
        print_status(True, "index.html found")
    else:
        print_status(False, "index.html not found")
    
    # Final recommendations
    print_section("6. Recommendations")
    
    recommendations = []
    
    if not backend_running:
        recommendations.append("Start the backend server")
    
    if not client_id or not client_secret:
        recommendations.append("Configure Microsoft OAuth credentials in .env file")
    
    if not openai_key:
        recommendations.append("Configure OpenAI API key in .env file")
    
    if recommendations:
        print(f"{Colors.YELLOW}Action Items:{Colors.RESET}")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print(f"{Colors.GREEN}✅ All basic checks passed!{Colors.RESET}")
        print_info("If you're still having login issues, check:")
        print_info("1. Azure AD app redirect URIs match your frontend URL")
        print_info("2. API permissions are granted and admin consented")
        print_info("3. Browser console for specific error messages")
    
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")
    return True

def main():
    """Main entry point."""
    try:
        asyncio.run(test_microsoft_config())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error running tests: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()


