#!/usr/bin/env python3
"""
End-to-End API Test for User Response Flow

This test verifies the complete invitation response flow using API calls only.
It tests the core backend functionality without browser automation.
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "testuser2024@example.com"
TEST_USER_PASSWORD = "password123"

class E2EAPIFlowTest:
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
                print(f"✅ Login successful")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Login failed: {response.status} - {error_text}")
                return False
    
    async def test_create_test_invite(self):
        """Test creating a test invite where user is invited"""
        print("\n📧 SCENARIO 1: Create Test Invitation")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with self.session.post(f"{BASE_URL}/activities/create-test-invite", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self.activity_id = data.get("id")
                print(f"✅ Test invite created successfully")
                print(f"   Activity ID: {self.activity_id}")
                print(f"   Title: {data.get('title')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Invitees: {len(data.get('invitees', []))}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Test invite creation failed: {response.status} - {error_text}")
                return False
    
    async def test_dashboard_visibility(self):
        """Test that the activity appears on user's dashboard"""
        print("\n👀 SCENARIO 2: Dashboard Visibility")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with self.session.get(f"{BASE_URL}/activities", headers=headers) as response:
            if response.status == 200:
                activities = await response.json()
                
                # Find the activity we just created
                invited_activity = None
                for activity in activities:
                    if activity.get("id") == self.activity_id:
                        invited_activity = activity
                        break
                
                if invited_activity:
                    print(f"✅ Activity visible on user's dashboard")
                    print(f"   Activity: {invited_activity.get('title')}")
                    print(f"   Status: {invited_activity.get('status')}")
                    print(f"   User is organizer: {invited_activity.get('organizer_id') == 'current_user'}")
                    
                    # Check if user is in invitees list
                    invitees = invited_activity.get('invitees', [])
                    user_invited = any(inv.get('email') == TEST_USER_EMAIL for inv in invitees)
                    
                    if user_invited:
                        print(f"✅ User correctly listed as invitee")
                        return True
                    else:
                        print(f"❌ User not found in invitees list")
                        return False
                else:
                    print(f"❌ Activity not found on dashboard")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Failed to get activities: {response.status} - {error_text}")
                return False
    
    async def test_user_response_submission(self):
        """Test submitting a user response"""
        print("\n📤 SCENARIO 3: User Response Submission")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response_data = {
            "response": "yes",
            "availabilityNote": "I'm available all weekend! Looking forward to it.",
            "venueSuggestion": "How about that new café downtown? They have great brunch!",
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
                print(f"✅ Response submitted successfully")
                print(f"   Message: {data.get('message')}")
                print(f"   Response recorded: {data.get('response_recorded')}")
                print(f"   Activity: {data.get('activity_title')}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Response submission failed: {response.status} - {error_text}")
                return False
    
    async def test_activity_summary(self):
        """Test getting activity summary"""
        print("\n📊 SCENARIO 4: Activity Summary")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with self.session.get(f"{BASE_URL}/activities/{self.activity_id}/summary", 
                                  headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                summary = data.get("summary", {})
                activity = data.get("activity", {})
                
                print(f"✅ Activity summary retrieved successfully")
                print(f"   Activity: {activity.get('title')}")
                print(f"   Total invitees: {summary.get('total_invitees')}")
                print(f"   Response rate: {summary.get('response_rate')}%")
                print(f"   Responses: {summary.get('responses')}")
                
                # Check venue suggestions
                venue_suggestions = summary.get("venue_suggestions", [])
                if venue_suggestions:
                    print(f"   Venue suggestions:")
                    for suggestion in venue_suggestions:
                        print(f"     - {suggestion.get('name')}: {suggestion.get('suggestion')}")
                
                # Check availability notes
                availability_notes = summary.get("availability_notes", [])
                if availability_notes:
                    print(f"   Availability notes:")
                    for note in availability_notes:
                        print(f"     - {note.get('name')}: {note.get('note')}")
                
                return True
            else:
                error_text = await response.text()
                print(f"❌ Activity summary failed: {response.status} - {error_text}")
                return False
    
    async def test_notifications(self):
        """Test getting notifications"""
        print("\n🔔 SCENARIO 5: Notifications")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with self.session.get(f"{BASE_URL}/notifications", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                notifications = data.get("notifications", [])
                print(f"✅ Retrieved {len(notifications)} notifications")
                
                # Look for activity-related notifications
                activity_notifications = [n for n in notifications 
                                        if "activity" in n.get("notification_type", "").lower()]
                
                if activity_notifications:
                    print(f"   Found {len(activity_notifications)} activity notifications")
                    for notif in activity_notifications[:3]:  # Show first 3
                        print(f"     - {notif.get('message')}")
                        print(f"       Type: {notif.get('notification_type')}")
                        print(f"       Read: {notif.get('read')}")
                
                return True
            else:
                error_text = await response.text()
                print(f"❌ Notifications retrieval failed: {response.status} - {error_text}")
                return False
    
    async def run_complete_api_test(self):
        """Run the complete API test flow"""
        print("🚀 Starting Complete API Flow Test")
        print("=" * 60)
        
        success_count = 0
        total_tests = 5
        
        try:
            await self.setup_session()
            
            # Login user
            if not await self.login_user():
                print("❌ Failed to login user, aborting test")
                return False
            
            # Test Scenario 1: Create test invite
            if await self.test_create_test_invite():
                success_count += 1
            
            # Test Scenario 2: Dashboard visibility
            if await self.test_dashboard_visibility():
                success_count += 1
            
            # Test Scenario 3: Response submission
            if await self.test_user_response_submission():
                success_count += 1
            
            # Test Scenario 4: Activity summary
            if await self.test_activity_summary():
                success_count += 1
            
            # Test Scenario 5: Notifications
            if await self.test_notifications():
                success_count += 1
            
            print("\n" + "=" * 60)
            print(f"📊 API TEST RESULTS: {success_count}/{total_tests} scenarios passed")
            
            if success_count == total_tests:
                print("🎉 ALL API TESTS PASSED! The backend flow is working correctly!")
                return True
            else:
                print(f"⚠️ {total_tests - success_count} test(s) failed. Check the implementation.")
                return False
                
        except Exception as e:
            print(f"\n💥 Test failed with exception: {str(e)}")
            return False
        
        finally:
            await self.cleanup_session()

async def main():
    """Main test function"""
    test_runner = E2EAPIFlowTest()
    success = await test_runner.run_complete_api_test()
    
    if success:
        print("\n🎉 API Flow implementation is working correctly!")
        print("✅ Backend scenarios completed successfully:")
        print("   1. ✅ Test Invitation Creation")
        print("   2. ✅ Dashboard Visibility") 
        print("   3. ✅ Response Submission")
        print("   4. ✅ Activity Summary")
        print("   5. ✅ Notifications")
    else:
        print("\n💥 Some API tests failed. Check the backend implementation.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())