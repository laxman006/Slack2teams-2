#!/usr/bin/env python3
"""
Security Test Script - IDOR Vulnerability Fix Verification

This script tests that the IDOR vulnerability has been fixed by attempting
various unauthorized access scenarios.

Usage:
    python test_security_fix.py
    
Requirements:
    - Server must be running
    - Need valid Microsoft OAuth token for testing
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Change to https://ai.cloudfuze.com for production
COLORS = {
    'GREEN': '\033[92m',
    'RED': '\033[91m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'RESET': '\033[0m'
}

class SecurityTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def print_header(self, text):
        print(f"\n{COLORS['BLUE']}{'='*70}{COLORS['RESET']}")
        print(f"{COLORS['BLUE']}{text.center(70)}{COLORS['RESET']}")
        print(f"{COLORS['BLUE']}{'='*70}{COLORS['RESET']}\n")
    
    def print_test(self, test_name, result, message):
        if result == "PASS":
            icon = "✅"
            color = COLORS['GREEN']
            self.passed += 1
        elif result == "FAIL":
            icon = "❌"
            color = COLORS['RED']
            self.failed += 1
        else:  # WARNING
            icon = "⚠️"
            color = COLORS['YELLOW']
            self.warnings += 1
            
        print(f"{icon} {color}{test_name}{COLORS['RESET']}")
        if message:
            print(f"   {message}")
        print()
    
    def test_no_auth_rejected(self):
        """Test 1: Requests without authentication should be rejected"""
        self.print_header("Test 1: Authentication Required")
        
        test_user_id = "test-user-123"
        
        try:
            response = requests.get(
                f"{self.base_url}/chat/history/{test_user_id}",
                timeout=5
            )
            
            if response.status_code == 401:
                self.print_test(
                    "No Auth Token → 401 Unauthorized",
                    "PASS",
                    f"Server correctly rejected request without token"
                )
            elif response.status_code == 403:
                self.print_test(
                    "No Auth Token → 403 Forbidden",
                    "PASS",
                    f"Server correctly rejected request (403 also acceptable)"
                )
            else:
                self.print_test(
                    "No Auth Token",
                    "FAIL",
                    f"Expected 401/403, got {response.status_code} - SECURITY ISSUE!"
                )
        except requests.exceptions.ConnectionError:
            self.print_test(
                "Connection Test",
                "WARNING",
                f"Cannot connect to {self.base_url}. Is the server running?"
            )
        except Exception as e:
            self.print_test("No Auth Test", "FAIL", f"Error: {str(e)}")
    
    def test_with_token(self, token, user_id, target_user_id=None):
        """Test authenticated requests"""
        if target_user_id is None:
            target_user_id = user_id
            
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(
                f"{self.base_url}/chat/history/{target_user_id}",
                headers=headers,
                timeout=5
            )
            
            if user_id == target_user_id:
                # Accessing own data
                if response.status_code == 200:
                    self.print_test(
                        "Access Own History → 200 OK",
                        "PASS",
                        "User can access their own chat history"
                    )
                    return True
                else:
                    self.print_test(
                        "Access Own History",
                        "FAIL",
                        f"Cannot access own history! Status: {response.status_code}"
                    )
                    return False
            else:
                # IDOR attempt - accessing another user's data
                if response.status_code == 403:
                    self.print_test(
                        "IDOR Protection → 403 Forbidden",
                        "PASS",
                        "✨ IDOR vulnerability is FIXED! Cannot access other user's data"
                    )
                    return True
                elif response.status_code == 401:
                    self.print_test(
                        "IDOR Attempt → 401",
                        "PASS",
                        "Request rejected (401 also acceptable)"
                    )
                    return True
                else:
                    self.print_test(
                        "IDOR Protection",
                        "FAIL",
                        f"🚨 CRITICAL: Still vulnerable! Status: {response.status_code}"
                    )
                    if response.status_code == 200:
                        print(f"{COLORS['RED']}   SECURITY BREACH: Successfully accessed another user's data!{COLORS['RESET']}")
                    return False
                    
        except requests.exceptions.ConnectionError:
            self.print_test(
                "Connection Test",
                "WARNING",
                f"Cannot connect to {self.base_url}"
            )
            return False
        except Exception as e:
            self.print_test("Token Test", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_endpoint_protection(self, endpoint, method="GET"):
        """Test if endpoint requires authentication"""
        try:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", json={}, timeout=5)
            elif method == "DELETE":
                response = requests.delete(f"{self.base_url}{endpoint}", timeout=5)
            
            if response.status_code in [401, 403]:
                return "PROTECTED"
            else:
                return f"EXPOSED ({response.status_code})"
                
        except requests.exceptions.ConnectionError:
            return "NO_CONNECTION"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def run_automated_tests(self):
        """Run tests that don't require real tokens"""
        self.print_header("🔒 Security Test Suite - IDOR Vulnerability Fix")
        
        print(f"Testing server: {COLORS['YELLOW']}{self.base_url}{COLORS['RESET']}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Test 1: No authentication
        self.test_no_auth_rejected()
        
        # Test 2: Endpoint protection check
        self.print_header("Test 2: Endpoint Protection Status")
        
        endpoints = [
            ("/chat/history/test-user", "GET"),
            ("/chat/history/test-user", "DELETE"),
            ("/dataset/corrected-responses", "GET"),
            ("/fine-tuning/status", "GET"),
        ]
        
        for endpoint, method in endpoints:
            status = self.test_endpoint_protection(endpoint, method)
            if status == "PROTECTED":
                self.print_test(
                    f"{method} {endpoint}",
                    "PASS",
                    "Endpoint requires authentication ✅"
                )
            elif status == "NO_CONNECTION":
                self.print_test(
                    f"{method} {endpoint}",
                    "WARNING",
                    "Cannot test - server not reachable"
                )
            else:
                self.print_test(
                    f"{method} {endpoint}",
                    "FAIL",
                    f"Endpoint may be exposed: {status}"
                )
        
        # Print summary
        self.print_summary()
    
    def run_manual_tests(self, user_a_token, user_a_id, user_b_id):
        """Run tests with real user tokens"""
        self.print_header("Test 3: IDOR Protection (Requires Real Tokens)")
        
        print(f"User A ID: {user_a_id}")
        print(f"User B ID: {user_b_id}\n")
        
        # Test accessing own history
        self.test_with_token(user_a_token, user_a_id, user_a_id)
        
        # Test IDOR - accessing another user's history
        self.test_with_token(user_a_token, user_a_id, user_b_id)
        
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        total = self.passed + self.failed + self.warnings
        
        print(f"\n{COLORS['BLUE']}{'='*70}{COLORS['RESET']}")
        print(f"{COLORS['BLUE']}TEST SUMMARY{COLORS['RESET']}")
        print(f"{COLORS['BLUE']}{'='*70}{COLORS['RESET']}\n")
        
        print(f"Total Tests: {total}")
        print(f"{COLORS['GREEN']}✅ Passed: {self.passed}{COLORS['RESET']}")
        print(f"{COLORS['RED']}❌ Failed: {self.failed}{COLORS['RESET']}")
        print(f"{COLORS['YELLOW']}⚠️  Warnings: {self.warnings}{COLORS['RESET']}\n")
        
        if self.failed == 0 and self.warnings == 0:
            print(f"{COLORS['GREEN']}🎉 ALL TESTS PASSED! Security fix is working!{COLORS['RESET']}\n")
        elif self.failed == 0:
            print(f"{COLORS['YELLOW']}⚠️  Tests passed but with warnings (likely server not running){COLORS['RESET']}\n")
        else:
            print(f"{COLORS['RED']}🚨 SECURITY ISSUES DETECTED! Review failed tests above.{COLORS['RESET']}\n")
        
        return self.failed == 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test IDOR vulnerability fix')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='Base URL of the API (default: http://localhost:8000)')
    parser.add_argument('--token', help='User A access token (for manual tests)')
    parser.add_argument('--user-id', help='User A ID')
    parser.add_argument('--other-user-id', help='User B ID (for IDOR testing)')
    
    args = parser.parse_args()
    
    tester = SecurityTester(args.url)
    
    # Always run automated tests
    tester.run_automated_tests()
    
    # Run manual tests if tokens provided
    if args.token and args.user_id and args.other_user_id:
        print(f"\n{COLORS['BLUE']}Running manual tests with provided credentials...{COLORS['RESET']}\n")
        tester.run_manual_tests(args.token, args.user_id, args.other_user_id)
    else:
        print(f"\n{COLORS['YELLOW']}ℹ️  For complete IDOR testing, run with real tokens:{COLORS['RESET']}")
        print(f"   python test_security_fix.py --token YOUR_TOKEN --user-id YOUR_ID --other-user-id OTHER_ID\n")
    
    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == "__main__":
    main()

