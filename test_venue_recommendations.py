#!/usr/bin/env python3
"""
Test script to verify the venue recommendations integration works correctly.
"""

import asyncio
import json
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.llm import llm_service
from backend.utils.environment import load_secrets_from_mongodb

async def setup_environment():
    """Setup environment by loading secrets from MongoDB."""
    print("Setting up environment...")
    
    # Get MongoDB connection details
    mongodb_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME", "sunnyside")
    
    if not mongodb_uri:
        print("⚠ MONGODB_URI not found in environment variables")
        return False
    
    try:
        # Connect to MongoDB
        mongodb_client = AsyncIOMotorClient(mongodb_uri)
        
        # Load secrets from MongoDB
        await load_secrets_from_mongodb(mongodb_client, database_name)
        
        # Close the connection
        mongodb_client.close()
        
        return True
    except Exception as e:
        print(f"⚠ Failed to setup environment: {e}")
        return False

async def test_venue_recommendations():
    """Test the venue recommendations with real context data."""
    print("Testing venue recommendations with real context...")
    
    # Test data
    query = "outdoor activities for friends"
    weather_data = {
        "current": {
            "temperature": 20,
            "weather_description": "sunny",
            "humidity": 60
        }
    }
    
    try:
        result = await llm_service.get_recommendations(
            query=query,
            max_results=3,
            weather_data=weather_data,
            date="2024-01-20",
            indoor_outdoor_preference="outdoor",
            location="Amsterdam",
            group_size=4,
            suggestion_type="specific"  # Use "specific" to get venue-based recommendations
        )
        
        print("✅ API call successful!")
        print(f"Success: {result.get('success')}")
        print(f"Number of recommendations: {len(result.get('recommendations', []))}")
        print(f"Venues found: {result.get('metadata', {}).get('venues_found', 0)}")
        
        # Print first recommendation as example
        if result.get('recommendations'):
            first_rec = result['recommendations'][0]
            print(f"\nExample recommendation:")
            print(f"Title: {first_rec.get('title')}")
            print(f"Description: {first_rec.get('description')}")
            if first_rec.get('venue'):
                venue = first_rec['venue']
                print(f"Venue: {venue.get('name')} - {venue.get('address')}")
                print(f"Link: {venue.get('link')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def test_venue_search():
    """Test the venue search functionality directly."""
    print("\nTesting venue search functionality...")
    
    try:
        venues = await llm_service._search_venues("hiking", "Amsterdam")
        print(f"✅ Venue search successful!")
        print(f"Found {len(venues)} venues")
        
        for i, venue in enumerate(venues, 1):
            print(f"{i}. {venue.get('name')} - {venue.get('source')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Venue search failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Testing Mistral AI Venue Recommendations Integration\n")
    
    # Setup environment first
    setup_success = await setup_environment()
    if not setup_success:
        print("❌ Failed to setup environment. Exiting.")
        return 1
    
    print("✅ Environment setup complete\n")
    
    # Test venue search
    search_success = await test_venue_search()
    
    # Test full recommendations
    rec_success = await test_venue_recommendations()
    
    print(f"\n📊 Test Results:")
    print(f"Environment Setup: {'✅ PASS' if setup_success else '❌ FAIL'}")
    print(f"Venue Search: {'✅ PASS' if search_success else '❌ FAIL'}")
    print(f"Recommendations: {'✅ PASS' if rec_success else '❌ FAIL'}")
    
    if setup_success and search_success and rec_success:
        print("\n🎉 All tests passed! The integration is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)