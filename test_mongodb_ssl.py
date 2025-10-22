#!/usr/bin/env python3
"""
Test MongoDB connection with SSL troubleshooting.
This script helps diagnose and fix SSL connection issues.
"""

import asyncio
import ssl
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URL, MONGODB_DATABASE, MONGODB_CHAT_COLLECTION

async def test_mongodb_ssl():
    """Test MongoDB connection with different SSL configurations."""
    
    print("MongoDB SSL Connection Test")
    print("=" * 40)
    print(f"URL: {MONGODB_URL}")
    print(f"Database: {MONGODB_DATABASE}")
    print(f"Collection: {MONGODB_CHAT_COLLECTION}")
    print()
    
    # Test configurations
    configs = [
        {
            "name": "Atlas/Cloud (SSL Required)",
            "config": {
                "tls": True,
                "tlsAllowInvalidCertificates": False,
                "tlsAllowInvalidHostnames": False,
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 10000,
                "socketTimeoutMS": 10000
            }
        },
        {
            "name": "Local MongoDB (No SSL)",
            "config": {
                "tls": False,
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 10000,
                "socketTimeoutMS": 10000
            }
        },
        {
            "name": "Local MongoDB (SSL with invalid certs allowed)",
            "config": {
                "tls": True,
                "tlsAllowInvalidCertificates": True,
                "tlsAllowInvalidHostnames": True,
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 10000,
                "socketTimeoutMS": 10000
            }
        }
    ]
    
    # Determine which configs to test based on URL
    is_atlas = "mongodb+srv://" in MONGODB_URL or "mongodb.net" in MONGODB_URL
    
    if is_atlas:
        print("Detected MongoDB Atlas connection - testing SSL configurations...")
        test_configs = [configs[0]]  # Only test Atlas config
    else:
        print("Detected local MongoDB connection - testing multiple configurations...")
        test_configs = configs[1:]  # Test local configs
    
    successful_config = None
    
    for config in test_configs:
        print(f"\nTesting: {config['name']}")
        print("-" * 30)
        
        try:
            client = AsyncIOMotorClient(MONGODB_URL, **config['config'])
            
            # Test connection
            await client.admin.command('ping')
            
            # Test database access
            db = client[MONGODB_DATABASE]
            collection = db[MONGODB_CHAT_COLLECTION]
            
            # Test collection operations
            count = await collection.count_documents({})
            
            print(f"SUCCESS! Connection established")
            print(f"   Database: {MONGODB_DATABASE}")
            print(f"   Collection: {MONGODB_CHAT_COLLECTION}")
            print(f"   Document count: {count}")
            
            successful_config = config
            await client.close()
            break
            
        except Exception as e:
            print(f"FAILED: {str(e)}")
            try:
                await client.close()
            except:
                pass
    
    print("\n" + "=" * 50)
    
    if successful_config:
        print("CONNECTION SUCCESSFUL!")
        print(f"Working configuration: {successful_config['name']}")
        print("\nRecommended .env settings:")
        print("=" * 30)
        
        if is_atlas:
            print("# For MongoDB Atlas")
            print("MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/")
            print("# No additional SSL settings needed - Atlas handles SSL automatically")
        else:
            if successful_config['name'] == "Local MongoDB (No SSL)":
                print("# For local MongoDB without SSL")
                print("MONGODB_URL=mongodb://localhost:27017")
            else:
                print("# For local MongoDB with SSL")
                print("MONGODB_URL=mongodb://localhost:27017")
                print("# SSL settings are handled automatically in the code")
        
        print("\nYour MongoDB connection is working!")
        print("You can now run the migration script and start your server.")
        
    else:
        print("ALL CONNECTION ATTEMPTS FAILED")
        print("\nTroubleshooting steps:")
        print("1. Check if MongoDB is running")
        print("2. Verify your connection URL")
        print("3. Check firewall settings")
        print("4. For Atlas: verify username/password and network access")
        print("5. For local: check if SSL is required in MongoDB config")
        
        print("\nCommon solutions:")
        print("- Local MongoDB: Try 'mongodb://localhost:27017'")
        print("- Atlas: Make sure IP is whitelisted and credentials are correct")
        print("- SSL issues: The code now handles SSL automatically")
    
    return successful_config is not None

async def main():
    """Main test function."""
    try:
        success = await test_mongodb_ssl()
        return success
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        return False
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())
