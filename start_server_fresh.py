"""
Start server with fresh load (no cache)
This ensures ChromaDB loads without any cached results
"""

import os
import sys

# Clear environment variables that might cause caching
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Don't write .pyc files
os.environ['CHROMADB_CACHE'] = '0'  # Disable ChromaDB internal caching if supported

print("=" * 80)
print("STARTING SERVER WITH FRESH LOAD (NO CACHE)")
print("=" * 80)
print()
print("Environment settings:")
print(f"  - PYTHONDONTWRITEBYTECODE: {os.environ.get('PYTHONDONTWRITEBYTECODE')}")
print(f"  - Working directory: {os.getcwd()}")
print()
print("Loading server components...")
print()

# Import and start server
try:
    import uvicorn
    from server import app
    from config import INITIALIZE_VECTORSTORE
    
    print(f"  - INITIALIZE_VECTORSTORE: {INITIALIZE_VECTORSTORE}")
    print()
    
    # Start server
    print("=" * 80)
    print("SERVER STARTING - N-GRAM BOOSTING ACTIVE")
    print("=" * 80)
    print()
    print("Test these queries to verify N-gram boosting:")
    print("  1. 'how does JSON Slack to Teams migration work'")
    print("  2. 'what API access does CloudFuze support'")
    print("  3. 'are migration logs available for OneDrive transfers'")
    print()
    print("Look for these logs:")
    print("  [N-GRAM] Detected X technical phrases: [...]")
    print("  [N-GRAM] Technical score: X.XX")
    print("  [N-GRAM BOOST] Reranking documents...")
    print()
    print("=" * 80)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        reload=False,  # No auto-reload (can cause caching)
        log_level="info"
    )
    
except KeyboardInterrupt:
    print("\n\nServer stopped by user")
    sys.exit(0)
except Exception as e:
    print(f"\n\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

