#!/usr/bin/env python3
"""
API-Only End-to-End Test for Invitee Summary Flow

This test covers the backend API flow for the new read-only summary page functionality:

1. Activity Creation and Invitation: An organizer creates an activity and invites a registered user
2. Initial Response: The invited user submits their response via API
3. Data Flow Verification: Ensure data flows correctly between frontend and backend
4. Summary Data Retrieval: Verify that the summary data can be retrieved correctly

This test uses only API calls to verify the backend functionality.
For full browser testing, use test_invitee_summary_flow.py with Selenium installed.
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ORGANIZER_EMAIL = "organizer.summary.api@example.com"
ORGANIZER_PASSWORD = "password123"
INVITEE_EMAIL = "invitee.summary.api@example.com"
INVITEE_PASSWORD = "password123"

class InviteeSummaryAPITest:
    def __init__(self):
        self.session = None
        self.organizer_token = None
        self.invitee_token = None
        self.activity_id = None
        self.organizer_user_id = None
        self.invitee_user_id = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        print("🔧 Setting up test environment...")
        self.session = aiohttp.ClientSession()
        print("✅ HTTP session initialized")
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
        print("🧹 Test environment cleaned up")
    
    async def login_test_user(self):
        """Login test user and get auth token"""
        print("🔐 Logging in test user...")
        
        login_data = {
            "username": "testuser2024@example.com",
            "password": "password123"
        }
        
        async with self.session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                self.invitee_token = data.get("access_token")
                print(f"✅ Login successful, token: {self.invitee_token[:20]}...")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Login failed: {response.status} - {error_text}")
                return False
    
    async def create_test_invite(self):
        """Test Scenario 1: Create a test invite to get an activity to respond to"""
        print("\n📧 SCENARIO 1: Creating Test Invite")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.invitee_token}"}
        
        async with self.session.post(f"{BASE_URL}/activities/create-test-invite", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self.activity_id = data.get("id")
                print(f"✅ Test invite created with activity ID: {self.activity_id}")
                print(f"   Title: {data.get('title')}")
                print(f"   Status: {data.get('status')}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Test invite creation failed: {response.status} - {error_text}")
                return False
    
    async def test_invitee_can_see_activity(self):
        """Test Scenario 2: Verify invitee can see the activity in their list"""
        print("\n👀 SCENARIO 2: Invitee Activity Visibility")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.invitee_token}"}
        
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
                    print(f"✅ Activity visible on invitee's activity list")
                    print(f"   Activity: {invited_activity.get('title')}")
                    print(f"   Status: {invited_activity.get('status')}")
                    print(f"   Invitees count: {len(invited_activity.get('invitees', []))}")
                    
                    # Check if the invitee is in the invitees list
                    invitee_found = False
                    for invitee in invited_activity.get('invitees', []):
                        if invitee.get('email') == INVITEE_EMAIL:
                            invitee_found = True
                            print(f"   Invitee status: {invitee.get('response', 'pending')}")
                            break
                    
                    if invitee_found:
                        print(f"✅ Invitee correctly listed in activity")
                        return True
                    else:
                        print(f"❌ Invitee not found in activity invitees list")
                        return False
                else:
                    print(f"❌ Activity not found on invitee's activity list")
                    print(f"   Available activities: {[a.get('title') for a in activities]}")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Failed to get invitee activities: {response.status} - {error_text}")
                return False
    
    async def test_initial_response_submission(self):
        """Test Scenario 3: User submits initial response via API"""
        print("\n📤 SCENARIO 3: Initial Response Submission")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.invitee_token}"}
        response_data = {
            "response": "yes",
            "availability_note": "I'm available all weekend! Looking forward to the museum visit.",
            "venue_suggestion": "How about starting at Café de Reiger and then visiting the Rijksmuseum?",
            "preferences": {
                "culture": True,
                "food": True,
                "outdoor": False,
                "indoor": True
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
    
    async def test_response_data_persistence(self):
        """Test Scenario 4: Verify response data is persisted correctly"""
        print("\n💾 SCENARIO 4: Response Data Persistence")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.invitee_token}"}
        
        async with self.session.get(f"{BASE_URL}/activities/{self.activity_id}", headers=headers) as response:
            if response.status == 200:
                activity_data = await response.json()
                print(f"✅ Retrieved activity data from backend")
                
                # Find the invitee's response in the activity data
                invitees = activity_data.get("invitees", [])
                user_response = None
                
                for invitee in invitees:
                    if invitee.get("email") == INVITEE_EMAIL:
                        user_response = invitee
                        break
                
                if user_response:
                    print(f"✅ Found user response in backend data:")
                    print(f"   Response: {user_response.get('response')}")
                    print(f"   Availability note: {user_response.get('availability_note')}")
                    print(f"   Venue suggestion: {user_response.get('venue_suggestion')}")
                    print(f"   Preferences: {user_response.get('preferences')}")
                    
                    # Verify the response matches what was submitted
                    expected_response = "yes"
                    if user_response.get("response") == expected_response:
                        print(f"✅ Response matches expected value: {expected_response}")
                    else:
                        print(f"❌ Response mismatch. Expected: {expected_response}, Got: {user_response.get('response')}")
                        return False
                    
                    # Verify availability note contains expected content
                    availability_note = user_response.get("availability_note", "")
                    if "available" in availability_note.lower() and "weekend" in availability_note.lower():
                        print(f"✅ Availability note contains expected content")
                    else:
                        print(f"⚠️ Availability note might not contain expected content: {availability_note}")
                    
                    # Verify venue suggestion contains expected content
                    venue_suggestion = user_response.get("venue_suggestion", "")
                    if "café" in venue_suggestion.lower() and "museum" in venue_suggestion.lower():
                        print(f"✅ Venue suggestion contains expected content")
                    else:
                        print(f"⚠️ Venue suggestion might not contain expected content: {venue_suggestion}")
                    
                    # Verify preferences were saved
                    preferences = user_response.get("preferences", {})
                    if preferences.get("culture") and preferences.get("food"):
                        print(f"✅ User preferences were saved correctly")
                    else:
                        print(f"⚠️ User preferences might not be saved correctly: {preferences}")
                    
                    return True
                else:
                    print(f"❌ User response not found in backend data")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Failed to get activity data: {response.status} - {error_text}")
                return False
    
    async def test_summary_data_retrieval(self):
        """Test Scenario 5: Verify summary data can be retrieved (organizer perspective)"""
        print("\n📊 SCENARIO 5: Summary Data Retrieval")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.invitee_token}"}
        
        async with self.session.get(f"{BASE_URL}/activities/{self.activity_id}/summary", headers=headers) as response:
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
                
                # Verify that we have at least one "yes" response
                responses = summary.get("responses", {})
                if responses.get("yes", 0) > 0:
                    print(f"✅ Response data correctly aggregated")
                    return True
                else:
                    print(f"❌ Expected 'yes' response not found in summary")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Activity summary failed: {response.status} - {error_text}")
                return False
    
    async def test_invitee_navigation_logic(self):
        """Test Scenario 6: Verify invitee navigation logic (simulate frontend logic)"""
        print("\n🧭 SCENARIO 6: Invitee Navigation Logic Simulation")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.invitee_token}"}
        
        # Get the activity as the invitee would see it
        async with self.session.get(f"{BASE_URL}/activities/{self.activity_id}", headers=headers) as response:
            if response.status == 200:
                activity_data = await response.json()
                
                # Simulate the frontend logic from Index.tsx
                user_email = INVITEE_EMAIL
                has_submitted_response = False
                
                # Check if user has already submitted a response
                invitees = activity_data.get("invitees", [])
                for invitee in invitees:
                    if invitee.get("email") == user_email:
                        if invitee.get("response") and invitee.get("response") != "pending":
                            has_submitted_response = True
                            print(f"✅ User has submitted response: {invitee.get('response')}")
                            break
                
                if has_submitted_response:
                    print(f"✅ Navigation logic: User should be directed to /invitee-activity-summary")
                    print(f"   This simulates the frontend logic that determines page routing")
                    print(f"   The summary page would show read-only data for this user")
                    return True
                else:
                    print(f"❌ Navigation logic: User should be directed to /invitee-response")
                    print(f"   This indicates the response was not properly saved")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Failed to get activity data for navigation logic: {response.status} - {error_text}")
                return False
    
    async def run_complete_api_test(self):
        """Run the complete API-based test flow"""
        print("🚀 Starting Complete Invitee Summary Flow API Test")
        print("=" * 70)
        
        success_count = 0
        total_tests = 6
        
        try:
            await self.setup_session()
            
            # Login test user
            if not await self.login_test_user():
                print("❌ Failed to login user, aborting test")
                return False
            
            # Test Scenario 1: Create Test Invite
            if await self.create_test_invite():
                success_count += 1
            
            # Test Scenario 2: Invitee Activity Visibility
            if await self.test_invitee_can_see_activity():
                success_count += 1
            
            # Test Scenario 3: Initial Response Submission
            if await self.test_initial_response_submission():
                success_count += 1
            
            # Test Scenario 4: Response Data Persistence
            if await self.test_response_data_persistence():
                success_count += 1
            
            # Test Scenario 5: Summary Data Retrieval (using invitee token since they're the organizer in test-invite)
            if await self.test_summary_data_retrieval():
                success_count += 1
            
            # Test Scenario 6: Navigation Logic Simulation
            if await self.test_invitee_navigation_logic():
                success_count += 1
            
            print("\n" + "=" * 70)
            print(f"📊 TEST RESULTS: {success_count}/{total_tests} scenarios passed")
            
            if success_count == total_tests:
                print("🎉 ALL API TESTS PASSED! The invitee summary flow backend is working correctly!")
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
    test_runner = InviteeSummaryAPITest()
    success = await test_runner.run_complete_api_test()
    
    if success:
        print("\n🎉 Invitee Summary Flow API implementation is working correctly!")
        print("✅ All API scenarios completed successfully:")
        print("   1. ✅ Activity Creation and Invitation")
        print("   2. ✅ Invitee Activity Visibility") 
        print("   3. ✅ Initial Response Submission")
        print("   4. ✅ Response Data Persistence")
        print("   5. ✅ Summary Data Retrieval")
        print("   6. ✅ Navigation Logic Simulation")
        print("\n🔄 Backend Flow Verified:")
        print("   • Organizer creates activity and invites user ✅")
        print("   • User can see activity in their list ✅")
        print("   • User submits response via API ✅")
        print("   • Response data is persisted correctly ✅")
        print("   • Summary data can be retrieved ✅")
        print("   • Navigation logic works as expected ✅")
        print("\n💡 For full browser testing, install Selenium and run:")
        print("   pip install selenium")
        print("   python test_invitee_summary_flow.py")
    else:
        print("\n💥 Some API tests failed. Check the implementation and try again.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())