#!/usr/bin/env python3
"""
Test script for Smart Scheduling feature.

This script tests the complete Smart Scheduling workflow including:
- Backend service functionality
- API endpoint responses
- Calendar integration
- Weather consideration
- Fallback behavior
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.smart_scheduling import smart_scheduling_service
from backend.services.google_calendar import google_calendar_service
from backend.services.weather import weather_service

async def test_smart_scheduling_service():
    """Test the Smart Scheduling service directly."""
    print("🧠 Testing Smart Scheduling Service...")
    
    # Test data
    activity = {
        "title": "Team Lunch",
        "activity_type": "dining",
        "weather_preference": "indoor"
    }
    
    participants = [
        {
            "id": "user1",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "google_calendar_credentials": None
        },
        {
            "id": "user2",
            "name": "Bob Smith", 
            "email": "bob@example.com",
            "google_calendar_credentials": None
        }
    ]
    
    try:
        result = await smart_scheduling_service.suggest_optimal_times(
            activity=activity,
            participants=participants,
            date_range_days=7,
            max_suggestions=3
        )
        
        print(f"✅ Service test successful!")
        print(f"   - Success: {result.get('success')}")
        print(f"   - Suggestions: {len(result.get('suggestions', []))}")
        print(f"   - Participants analyzed: {result.get('participants_analyzed')}")
        print(f"   - Calendar data available: {result.get('calendar_data_available')}")
        print(f"   - Weather considered: {result.get('weather_considered')}")
        
        # Print first suggestion details
        suggestions = result.get('suggestions', [])
        if suggestions:
            first_suggestion = suggestions[0]
            print(f"   - First suggestion: {first_suggestion.get('start')} - {first_suggestion.get('end')}")
            print(f"   - Reasoning: {first_suggestion.get('reasoning')}")
            print(f"   - Confidence: {first_suggestion.get('confidence_score'):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {str(e)}")
        return False

async def test_outdoor_activity_with_weather():
    """Test Smart Scheduling with outdoor activity and weather consideration."""
    print("\n☀️ Testing Outdoor Activity with Weather...")
    
    activity = {
        "title": "Park Picnic",
        "activity_type": "outdoor",
        "weather_preference": "outdoor"
    }
    
    participants = [
        {
            "id": "user1",
            "name": "Charlie Brown",
            "email": "charlie@example.com",
            "google_calendar_credentials": None
        }
    ]
    
    try:
        result = await smart_scheduling_service.suggest_optimal_times(
            activity=activity,
            participants=participants,
            date_range_days=5,
            max_suggestions=3
        )
        
        print(f"✅ Outdoor activity test successful!")
        print(f"   - Weather considered: {result.get('weather_considered')}")
        
        suggestions = result.get('suggestions', [])
        if suggestions:
            for i, suggestion in enumerate(suggestions[:2]):
                print(f"   - Suggestion {i+1}: {suggestion.get('start')}")
                print(f"     Reasoning: {suggestion.get('reasoning')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Outdoor activity test failed: {str(e)}")
        return False

async def test_calendar_integration():
    """Test Google Calendar integration capabilities."""
    print("\n📅 Testing Calendar Integration...")
    
    try:
        # Test if Google Calendar service is available
        if google_calendar_service.enabled:
            print("✅ Google Calendar service is enabled")
            
            # Test authorization URL generation
            try:
                auth_url = google_calendar_service.get_authorization_url("test-state")
                print(f"✅ Authorization URL generated: {auth_url[:50]}...")
            except Exception as e:
                print(f"⚠️  Authorization URL generation failed: {str(e)}")
        else:
            print("⚠️  Google Calendar service is disabled (missing credentials)")
        
        # Test with mock calendar credentials
        participants_with_calendar = [
            {
                "id": "user1",
                "name": "David Wilson",
                "email": "david@example.com",
                "google_calendar_credentials": {
                    "access_token": "mock_token",
                    "refresh_token": "mock_refresh",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": "mock_client_id",
                    "client_secret": "mock_client_secret",
                    "scopes": ["https://www.googleapis.com/auth/calendar.readonly"]
                }
            }
        ]
        
        activity = {
            "title": "Business Meeting",
            "activity_type": "business",
            "weather_preference": "indoor"
        }
        
        result = await smart_scheduling_service.suggest_optimal_times(
            activity=activity,
            participants=participants_with_calendar,
            date_range_days=7,
            max_suggestions=3
        )
        
        print(f"✅ Calendar integration test completed")
        print(f"   - Participants with calendar: {result.get('calendar_data_available', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Calendar integration test failed: {str(e)}")
        return False

async def test_weather_service():
    """Test weather service integration."""
    print("\n🌤️  Testing Weather Service...")
    
    try:
        # Test weather forecast retrieval
        weather_data = await weather_service.get_weather_forecast(52.3676, 4.9041, 5)
        
        print(f"✅ Weather service test successful!")
        print(f"   - Location: {weather_data.get('location', {}).get('name', 'Unknown')}")
        print(f"   - Forecasts: {len(weather_data.get('forecasts', []))}")
        print(f"   - Source: {weather_data.get('source', 'Unknown')}")
        
        forecasts = weather_data.get('forecasts', [])
        if forecasts:
            first_forecast = forecasts[0]
            print(f"   - First forecast: {first_forecast.get('date')} - {first_forecast.get('weather_description')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Weather service test failed: {str(e)}")
        return False

async def test_fallback_behavior():
    """Test fallback behavior when services are unavailable."""
    print("\n🔄 Testing Fallback Behavior...")
    
    # Test with empty participants list
    try:
        result = await smart_scheduling_service.suggest_optimal_times(
            activity={"title": "Test Activity", "activity_type": "social"},
            participants=[],
            date_range_days=7,
            max_suggestions=3
        )
        
        print(f"✅ Empty participants test: {result.get('success')}")
        
    except Exception as e:
        print(f"⚠️  Empty participants test failed: {str(e)}")
    
    # Test with minimal activity data
    try:
        result = await smart_scheduling_service.suggest_optimal_times(
            activity={"title": "Minimal Activity"},
            participants=[{"name": "Test User", "email": "test@example.com"}],
            date_range_days=3,
            max_suggestions=2
        )
        
        print(f"✅ Minimal data test: {result.get('success')}")
        print(f"   - Suggestions generated: {len(result.get('suggestions', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback behavior test failed: {str(e)}")
        return False

def test_api_endpoint_structure():
    """Test API endpoint structure and imports."""
    print("\n🔌 Testing API Endpoint Structure...")
    
    try:
        # Test imports
        from backend.routes.llm import router
        from backend.services.smart_scheduling import smart_scheduling_service
        
        print("✅ All imports successful")
        print("✅ Smart scheduling service available")
        print("✅ LLM router available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {str(e)}")
        return False

async def run_all_tests():
    """Run all Smart Scheduling tests."""
    print("🚀 Starting Smart Scheduling Tests...\n")
    
    test_results = []
    
    # Test API structure
    test_results.append(test_api_endpoint_structure())
    
    # Test core service
    test_results.append(await test_smart_scheduling_service())
    
    # Test weather integration
    test_results.append(await test_weather_service())
    
    # Test outdoor activity with weather
    test_results.append(await test_outdoor_activity_with_weather())
    
    # Test calendar integration
    test_results.append(await test_calendar_integration())
    
    # Test fallback behavior
    test_results.append(await test_fallback_behavior())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 Test Results Summary:")
    print(f"   - Passed: {passed}/{total}")
    print(f"   - Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All Smart Scheduling tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    print("Smart Scheduling Feature Test Suite")
    print("=" * 50)
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)