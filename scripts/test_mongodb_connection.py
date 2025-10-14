#!/usr/bin/env python3
"""
MongoDB Atlas Connection Diagnostic Script
This script helps diagnose MongoDB Atlas connection issues.
"""

import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_mongodb_connection():
    """Test MongoDB Atlas connection with detailed diagnostics."""
    
    # Get connection details
    mongodb_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME", "sunnyside")
    
    print("=== MongoDB Atlas Connection Diagnostic ===")
    print(f"Database Name: {database_name}")
    print(f"Connection URI: {mongodb_uri[:50]}...{mongodb_uri[-20:] if len(mongodb_uri) > 70 else mongodb_uri}")
    print()
    
    if not mongodb_uri:
        print("❌ ERROR: MONGODB_URI environment variable not found")
        return False
    
    try:
        print("🔄 Creating MongoDB client...")
        client = AsyncIOMotorClient(mongodb_uri)
        
        print("🔄 Testing basic connection (ping)...")
        await client.admin.command('ping')
        print("✅ Basic connection successful!")
        
        print("🔄 Testing database access...")
        db = client[database_name]
        
        print("🔄 Testing collection access...")
        users_collection = db.users
        
        print("🔄 Counting documents in users collection...")
        count = await users_collection.count_documents({})
        print(f"✅ Users collection accessible. Document count: {count}")
        
        print("🔄 Testing write permissions...")
        test_doc = {"test": "connection_test", "timestamp": "2024-01-01"}
        result = await users_collection.insert_one(test_doc)
        print(f"✅ Write test successful. Inserted ID: {result.inserted_id}")
        
        print("🔄 Cleaning up test document...")
        await users_collection.delete_one({"_id": result.inserted_id})
        print("✅ Cleanup successful!")
        
        print("🔄 Testing server info...")
        server_info = await client.server_info()
        print(f"✅ MongoDB Server Version: {server_info.get('version', 'Unknown')}")
        
        print("\n🎉 All MongoDB Atlas connection tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed with error:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        # Specific error analysis
        error_str = str(e).lower()
        if "authentication failed" in error_str:
            print("\n🔍 DIAGNOSIS: Authentication Error")
            print("Possible causes:")
            print("1. Database user credentials are incorrect")
            print("2. Database user doesn't exist or is disabled")
            print("3. Database user doesn't have permissions for this database")
            print("4. Password contains special characters that need URL encoding")
            
        elif "network" in error_str or "timeout" in error_str:
            print("\n🔍 DIAGNOSIS: Network Error")
            print("Possible causes:")
            print("1. IP address not whitelisted in MongoDB Atlas")
            print("2. Network connectivity issues")
            print("3. Firewall blocking connection")
            
        elif "cluster" in error_str:
            print("\n🔍 DIAGNOSIS: Cluster Error")
            print("Possible causes:")
            print("1. MongoDB Atlas cluster is paused")
            print("2. Cluster name is incorrect")
            print("3. Cluster is not available in the specified region")
            
        return False
        
    finally:
        if 'client' in locals():
            client.close()
            print("🔄 Connection closed.")

async def test_connection_variations():
    """Test different connection string variations."""
    base_uri = os.getenv("MONGODB_URI")
    if not base_uri:
        return
    
    print("\n=== Testing Connection String Variations ===")
    
    # Test with explicit database in URI
    uri_with_db = base_uri.replace("/?", "/sunnyside?")
    print(f"🔄 Testing with database in URI: ...{uri_with_db[-50:]}")
    
    try:
        client = AsyncIOMotorClient(uri_with_db)
        await client.admin.command('ping')
        print("✅ Connection with database in URI successful!")
        client.close()
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

if __name__ == "__main__":
    print("Starting MongoDB Atlas connection diagnostics...\n")
    
    # Run the main test
    success = asyncio.run(test_mongodb_connection())
    
    if not success:
        # Run additional tests
        asyncio.run(test_connection_variations())
    
    print(f"\n{'='*50}")
    if success:
        print("✅ MongoDB Atlas connection is working properly!")
    else:
        print("❌ MongoDB Atlas connection has issues that need to be resolved.")
        print("\nNext steps:")
        print("1. Check MongoDB Atlas dashboard for user permissions")
        print("2. Verify network access settings (IP whitelist)")
        print("3. Ensure cluster is running and not paused")
        print("4. Check if password needs URL encoding")