#!/usr/bin/env python3
"""
Quick test to verify auto-correction setup is working correctly
"""

import sys
import os

# Use ASCII symbols for Windows compatibility
CHECK = '[OK]'
CROSS = '[FAIL]'
WARN = '[WARN]'

def test_imports():
    """Test that all required modules can be imported"""
    print(f"\n{'='*70}")
    print("Testing imports...")
    print(f"{'='*70}\n")
    
    tests = []
    
    # Test 1: Import langfuse
    try:
        from langfuse import Langfuse
        print(f"{CHECK} langfuse module imported")
        tests.append(True)
    except Exception as e:
        print(f"{CROSS} Failed to import langfuse: {e}")
        tests.append(False)
    
    # Test 2: Import endpoints
    try:
        from app.endpoints import generate_improved_response
        print(f"{CHECK} app.endpoints.generate_improved_response imported")
        tests.append(True)
    except Exception as e:
        print(f"{CROSS} Failed to import generate_improved_response: {e}")
        tests.append(False)
    
    # Test 3: Import langfuse_integration
    try:
        from app.langfuse_integration import langfuse_tracker
        print(f"{CHECK} app.langfuse_integration.langfuse_tracker imported")
        tests.append(True)
    except Exception as e:
        print(f"{CROSS} Failed to import langfuse_tracker: {e}")
        tests.append(False)
    
    # Test 4: Import auto_correct script
    try:
        sys.path.insert(0, 'scripts')
        from auto_correct_low_scores import AutoCorrectionProcessor
        print(f"{CHECK} AutoCorrectionProcessor class imported")
        tests.append(True)
    except Exception as e:
        print(f"{CROSS} Failed to import AutoCorrectionProcessor: {e}")
        tests.append(False)
    
    return all(tests)

def test_environment():
    """Test environment variables"""
    print(f"\n{'='*70}")
    print("Testing environment variables...")
    print(f"{'='*70}\n")
    
    tests = []
    
    # Test 1: LANGFUSE_PUBLIC_KEY
    from config import LANGFUSE_PUBLIC_KEY
    if LANGFUSE_PUBLIC_KEY:
        print(f"{CHECK} LANGFUSE_PUBLIC_KEY is set")
        tests.append(True)
    else:
        print(f"{CROSS} LANGFUSE_PUBLIC_KEY is not set")
        tests.append(False)
    
    # Test 2: LANGFUSE_SECRET_KEY
    from config import LANGFUSE_SECRET_KEY
    if LANGFUSE_SECRET_KEY:
        print(f"{CHECK} LANGFUSE_SECRET_KEY is set")
        tests.append(True)
    else:
        print(f"{CROSS} LANGFUSE_SECRET_KEY is not set")
        tests.append(False)
    
    # Test 3: OPENAI_API_KEY
    from config import OPENAI_API_KEY
    if OPENAI_API_KEY:
        print(f"{CHECK} OPENAI_API_KEY is set")
        tests.append(True)
    else:
        print(f"{CROSS} OPENAI_API_KEY is not set")
        tests.append(False)
    
    return all(tests)

def test_langfuse_connection():
    """Test Langfuse client connection"""
    print(f"\n{'='*70}")
    print("Testing Langfuse connection...")
    print(f"{'='*70}\n")
    
    try:
        from app.langfuse_integration import langfuse_tracker
        
        if langfuse_tracker and langfuse_tracker.client:
            print(f"{CHECK} Langfuse client is initialized")
            return True
        else:
            print(f"{CROSS} Langfuse client is not initialized")
            return False
    except Exception as e:
        print(f"{CROSS} Error testing Langfuse connection: {e}")
        return False

def test_vectorstore():
    """Test vectorstore availability"""
    print(f"\n{'='*70}")
    print("Testing vectorstore...")
    print(f"{'='*70}\n")
    
    try:
        from app.vectorstore import vectorstore
        
        if vectorstore:
            print(f"{CHECK} Vectorstore is initialized")
            return True
        else:
            print(f"{WARN} Vectorstore is not initialized (set INITIALIZE_VECTORSTORE=true in .env)")
            print(f"  Note: Auto-correction will still work but with limited context")
            return True  # Not a critical failure
    except Exception as e:
        print(f"{WARN} Error checking vectorstore: {e}")
        return True  # Not a critical failure

def test_files_exist():
    """Test that all required files exist"""
    print(f"\n{'='*70}")
    print("Testing file existence...")
    print(f"{'='*70}\n")
    
    files = [
        'scripts/auto_correct_low_scores.py',
        'run_auto_correction.bat',
        'run_auto_correction.sh',
        'AUTO-CORRECTION-GUIDE.md',
        'AUTO-CORRECTION-SETUP-COMPLETE.md',
        'app/langfuse_integration.py',
        'app/endpoints.py'
    ]
    
    tests = []
    for file_path in files:
        if os.path.exists(file_path):
            print(f"{CHECK} {file_path}")
            tests.append(True)
        else:
            print(f"{CROSS} {file_path} not found")
            tests.append(False)
    
    return all(tests)

def main():
    """Run all tests"""
    print(f"\n{'='*70}")
    print("AUTO-CORRECTION SETUP VERIFICATION")
    print(f"{'='*70}")
    
    results = []
    
    # Run tests
    results.append(("File Existence", test_files_exist()))
    results.append(("Python Imports", test_imports()))
    results.append(("Environment Variables", test_environment()))
    results.append(("Langfuse Connection", test_langfuse_connection()))
    results.append(("Vectorstore", test_vectorstore()))
    
    # Print summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}\n")
    
    all_passed = True
    for test_name, passed in results:
        if passed:
            print(f"{CHECK} {test_name}: PASSED")
        else:
            print(f"{CROSS} {test_name}: FAILED")
            all_passed = False
    
    print(f"\n{'='*70}")
    if all_passed:
        print(f"[OK] ALL TESTS PASSED!")
        print(f"{'='*70}\n")
        print("Auto-correction system is ready to use!")
        print("\nNext steps:")
        print("  1. Test with dry run:")
        print("     python scripts/auto_correct_low_scores.py --dry-run")
        print("\n  2. Run once:")
        print("     python scripts/auto_correct_low_scores.py")
        print("\n  3. Enable polling:")
        print("     python scripts/auto_correct_low_scores.py --poll --interval 300")
    else:
        print(f"[FAIL] SOME TESTS FAILED")
        print(f"{'='*70}\n")
        print("Please fix the issues above before using auto-correction.")
        print("\nCommon fixes:")
        print("  - Check .env file has LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        print("  - Run: pip install -r requirements.txt")
        print("  - Verify Langfuse credentials are correct")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

