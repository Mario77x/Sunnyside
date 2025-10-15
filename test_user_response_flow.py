#!/usr/bin/env python3
"""
Test script for the new user response flow functionality.
Tests the new API endpoints for registered user responses and notifications.
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "testuser2024@example.com"
TEST_USER_PASSWORD = "password123"

class TestUserResponseFlow:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.activity_id = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def login_user(self):
        """Login test user and get auth token"""
        print("🔐 Logging in test user...")
        
        login_data = {
            "username": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        async with self.session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                self.auth_token = data.get("access_token")
                print(f"✅ Login successful, token: {self.auth_token[:20]}...")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Login failed: {response.status} - {error_text}")
                return False
    
    async def create_test_activity(self):
        """Create a test activity"""
        print("📝 Creating test activity...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        activity_data = {
            "title": "Test User Response Activity",
            "description": "Testing the new user response flow",
            "timeframe": "weekend",
            "groupSize": "small group",
            "activityType": "food",
            "weatherPreference": "either",
            "selectedDate": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        async with self.session.post(f"{BASE_URL}/activities", json=activity_data, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self.activity_id = data.get("id")
                print(f"✅ Activity created with ID: {self.activity_id}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Activity creation failed: {response.status} - {error_text}")
                return False
    
    async def create_test_invite(self):
        """Create a test invite to get an activity to respond to"""
        print("📧 Creating test invite...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with self.session.post(f"{BASE_URL}/activities/create-test-invite", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self.activity_id = data.get("id")
                print(f"✅ Test invite created with activity ID: {self.activity_id}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Test invite creation failed: {response.status} - {error_text}")
                return False
    
    async def test_user_response_submission(self):
        """Test submitting a user response"""
        print("📤 Testing user response submission...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response_data = {
            "response": "yes",
            "availabilityNote": "I'm available all weekend! Looking forward to it.",
            "venueSuggestion": "How about that new restaurant downtown?",
            "preferences": {
                "food": True,
                "outdoor": True,
                "indoor": False
            }
        }
        
        async with self.session.post(f"{BASE_URL}/activities/{self.activity_id}/respond", 
                                   json=response_data, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Response submitted successfully: {data.get('message')}")
                print(f"   Response recorded: {data.get('response_recorded')}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Response submission failed: {response.status} - {error_text}")
                return False
    
    async def test_activity_summary(self):
        """Test getting activity summary (organizer view)"""
        print("📊 Testing activity summary endpoint...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with self.session.get(f"{BASE_URL}/activities/{self.activity_id}/summary", 
                                  headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Activity summary retrieved successfully")
                
                summary = data.get("summary", {})
                print(f"   Total invitees: {summary.get('total_invitees')}")
                print(f"   Response rate: {summary.get('response_rate')}%")
                print(f"   Responses: {summary.get('responses')}")
                
                venue_suggestions = summary.get("venue_suggestions", [])
                if venue_suggestions:
                    print("   Venue suggestions:")
                    for suggestion in venue_suggestions:
                        print(f"     - {suggestion.get('name')}: {suggestion.get('suggestion')}")
                
                availability_notes = summary.get("availability_notes", [])
                if availability_notes:
                    print("   Availability notes:")
                    for note in availability_notes:
                        print(f"     - {note.get('name')}: {note.get('note')}")
                
                return True
            else:
                error_text = await response.text()
                print(f"❌ Activity summary failed: {response.status} - {error_text}")
                return False
    
    async def test_notifications(self):
        """Test getting notifications"""
        print("🔔 Testing notifications...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with self.session.get(f"{BASE_URL}/notifications", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                notifications = data.get("notifications", [])
                print(f"✅ Retrieved {len(notifications)} notifications")
                
                # Look for activity response notifications
                response_notifications = [n for n in notifications if n.get("notification_type") == "activity_response"]
                if response_notifications:
                    print(f"   Found {len(response_notifications)} activity response notifications")
                    for notif in response_notifications[:3]:  # Show first 3
                        print(f"     - {notif.get('message')}")
                
                return True
            else:
                error_text = await response.text()
                print(f"❌ Notifications retrieval failed: {response.status} - {error_text}")
                return False
    
    async def run_tests(self):
        """Run all tests"""
        print("🚀 Starting User Response Flow Tests")
        print("=" * 50)
        
        await self.setup_session()
        
        try:
            # Test sequence
            if not await self.login_user():
                return False
            
            if not await self.create_test_activity():
                return False
            
            if not await self.test_user_response_submission():
                return False
            
            if not await self.test_activity_summary():
                return False
            
            if not await self.test_notifications():
                return False
            
            print("\n" + "=" * 50)
            print("✅ All tests completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with exception: {str(e)}")
            return False
        
        finally:
            await self.cleanup_session()

async def main():
    """Main test function"""
    test_runner = TestUserResponseFlow()
    success = await test_runner.run_tests()
    
    if success:
        print("\n🎉 User Response Flow implementation is working correctly!")
    else:
        print("\n💥 Some tests failed. Check the implementation.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())