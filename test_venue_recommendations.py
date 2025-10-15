#!/usr/bin/env python3
"""
Test script to verify the venue recommendations integration works correctly.
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.llm import llm_service

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
            group_size=4
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
    
    # Test venue search
    search_success = await test_venue_search()
    
    # Test full recommendations
    rec_success = await test_venue_recommendations()
    
    print(f"\n📊 Test Results:")
    print(f"Venue Search: {'✅ PASS' if search_success else '❌ FAIL'}")
    print(f"Recommendations: {'✅ PASS' if rec_success else '❌ FAIL'}")
    
    if search_success and rec_success:
        print("\n🎉 All tests passed! The integration is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)