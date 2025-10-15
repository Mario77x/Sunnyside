#!/usr/bin/env python3
"""
Test script to verify that organizers receive notifications when invited users respond to activities.
This test covers both registered users and guest users responding to activities.
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_ORGANIZER = {
    "name": "Test Organizer",
    "email": "organizer@test.com",
    "password": "testpass123"
}
TEST_REGISTERED_USER = {
    "name": "Registered User",
    "email": "registered@test.com", 
    "password": "testpass123"
}
TEST_GUEST_USER = {
    "name": "Guest User",
    "email": "guest@test.com"
}

class NotificationTester:
    def __init__(self):
        self.organizer_token = None
        self.registered_user_token = None
        self.activity_id = None
        
    async def setup_users(self):
        """Create test users and get authentication tokens."""
        print("🔧 Setting up test users...")
        
        async with httpx.AsyncClient() as client:
            # Create organizer
            try:
                response = await client.post(f"{BASE_URL}/auth/signup", json=TEST_ORGANIZER)
                if response.status_code == 200:
                    print(f"✅ Created organizer: {TEST_ORGANIZER['email']}")
                elif response.status_code == 500 and "already exists" in response.text:
                    print(f"ℹ️  Organizer already exists: {TEST_ORGANIZER['email']}")
                else:
                    print(f"❌ Failed to create organizer: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Error creating organizer: {e}")
            
            # Create registered user
            try:
                response = await client.post(f"{BASE_URL}/auth/signup", json=TEST_REGISTERED_USER)
                if response.status_code == 200:
                    print(f"✅ Created registered user: {TEST_REGISTERED_USER['email']}")
                elif response.status_code == 500 and "already exists" in response.text:
                    print(f"ℹ️  Registered user already exists: {TEST_REGISTERED_USER['email']}")
                else:
                    print(f"❌ Failed to create registered user: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Error creating registered user: {e}")
            
            # Login organizer
            login_data = {"username": TEST_ORGANIZER["email"], "password": TEST_ORGANIZER["password"]}
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                self.organizer_token = response.json()["access_token"]
                print(f"✅ Organizer logged in successfully")
            else:
                print(f"❌ Failed to login organizer: {response.status_code} - {response.text}")
                return False
            
            # Login registered user
            login_data = {"username": TEST_REGISTERED_USER["email"], "password": TEST_REGISTERED_USER["password"]}
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                self.registered_user_token = response.json()["access_token"]
                print(f"✅ Registered user logged in successfully")
            else:
                print(f"❌ Failed to login registered user: {response.status_code} - {response.text}")
                return False
                
        return True
    
    async def create_test_activity(self):
        """Create a test activity as the organizer."""
        print("\n🎯 Creating test activity...")
        
        activity_data = {
            "title": "Notification Test Activity",
            "description": "Testing notification system for activity responses",
            "timeframe": "This weekend",
            "groupSize": "small group",
            "activityType": "social",
            "weatherPreference": "either",
            "selectedDate": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        headers = {"Authorization": f"Bearer {self.organizer_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BASE_URL}/activities", json=activity_data, headers=headers)
            if response.status_code == 200:
                activity = response.json()
                self.activity_id = activity["id"]
                print(f"✅ Created activity: {activity['title']} (ID: {self.activity_id})")
                return True
            else:
                print(f"❌ Failed to create activity: {response.status_code} - {response.text}")
                return False
    
    async def invite_users_to_activity(self):
        """Invite both registered and guest users to the activity."""
        print("\n📧 Inviting users to activity...")
        
        invite_data = {
            "invitees": [
                {"name": TEST_REGISTERED_USER["name"], "email": TEST_REGISTERED_USER["email"]},
                {"name": TEST_GUEST_USER["name"], "email": TEST_GUEST_USER["email"]}
            ],
            "custom_message": "Please join us for this test activity!"
        }
        
        headers = {"Authorization": f"Bearer {self.organizer_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BASE_URL}/activities/{self.activity_id}/invite", json=invite_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Sent invitations to {result['invited_count']} users")
                print(f"   📧 Emails sent: {result['emails_sent']}")
                return True
            else:
                print(f"❌ Failed to send invitations: {response.status_code} - {response.text}")
                return False
    
    async def get_organizer_notifications_before(self):
        """Get organizer's notification count before responses."""
        print("\n📊 Checking organizer notifications before responses...")
        
        headers = {"Authorization": f"Bearer {self.organizer_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/notifications/unread-count", headers=headers)
            if response.status_code == 200:
                count = response.json()["unread_count"]
                print(f"📋 Organizer has {count} unread notifications before responses")
                return count
            else:
                print(f"❌ Failed to get notification count: {response.status_code} - {response.text}")
                return None
    
    async def submit_registered_user_response(self):
        """Submit response as registered user."""
        print("\n👤 Submitting registered user response...")
        
        response_data = {
            "response": "yes",
            "availabilityNote": "I'm available and excited to join!",
            "venueSuggestion": "How about the park downtown?"
        }
        
        headers = {"Authorization": f"Bearer {self.registered_user_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BASE_URL}/activities/{self.activity_id}/respond", json=response_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Registered user response submitted: {result['response_recorded']}")
                return True
            else:
                print(f"❌ Failed to submit registered user response: {response.status_code} - {response.text}")
                return False
    
    async def submit_guest_user_response(self):
        """Submit response as guest user."""
        print("\n👥 Submitting guest user response...")
        
        response_data = {
            "guest_id": TEST_GUEST_USER["email"],
            "response": "maybe",
            "availability_note": "I might be able to make it, depends on work",
            "venue_suggestion": "Maybe somewhere with parking?"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BASE_URL}/invites/{self.activity_id}/respond", json=response_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Guest user response submitted: {result['response_recorded']}")
                return True
            else:
                print(f"❌ Failed to submit guest user response: {response.status_code} - {response.text}")
                return False
    
    async def verify_organizer_notifications(self, initial_count):
        """Verify organizer received notifications for both responses."""
        print("\n🔍 Verifying organizer received notifications...")
        
        # Wait a moment for notifications to be processed
        await asyncio.sleep(2)
        
        headers = {"Authorization": f"Bearer {self.organizer_token}"}
        
        async with httpx.AsyncClient() as client:
            # Check unread count
            response = await client.get(f"{BASE_URL}/notifications/unread-count", headers=headers)
            if response.status_code == 200:
                new_count = response.json()["unread_count"]
                expected_count = initial_count + 2  # Should have 2 new notifications
                print(f"📋 Organizer now has {new_count} unread notifications (expected: {expected_count})")
                
                if new_count >= expected_count:
                    print("✅ Notification count increased as expected!")
                else:
                    print("❌ Notification count did not increase as expected!")
                    return False
            else:
                print(f"❌ Failed to get updated notification count: {response.status_code}")
                return False
            
            # Get actual notifications to verify content
            response = await client.get(f"{BASE_URL}/notifications", headers=headers)
            if response.status_code == 200:
                notifications = response.json()
                print(f"📋 Retrieved {len(notifications)} total notifications")
                
                # Look for our activity response notifications
                activity_notifications = [
                    n for n in notifications 
                    if n.get("notification_type") == "activity_response" and 
                       "Notification Test Activity" in n.get("message", "")
                ]
                
                print(f"🎯 Found {len(activity_notifications)} activity response notifications")
                
                if len(activity_notifications) >= 2:
                    print("✅ Found notifications for both user responses!")
                    for i, notif in enumerate(activity_notifications[:2]):
                        print(f"   📝 Notification {i+1}: {notif['message']}")
                    return True
                else:
                    print("❌ Did not find expected number of activity response notifications!")
                    print("📋 All notifications:")
                    for notif in notifications[:5]:  # Show first 5
                        print(f"   - {notif.get('notification_type', 'unknown')}: {notif.get('message', 'no message')}")
                    return False
            else:
                print(f"❌ Failed to get notifications: {response.status_code}")
                return False
    
    async def cleanup(self):
        """Clean up test data."""
        print("\n🧹 Cleaning up test data...")
        
        if self.activity_id and self.organizer_token:
            headers = {"Authorization": f"Bearer {self.organizer_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{BASE_URL}/activities/{self.activity_id}", headers=headers)
                if response.status_code == 200:
                    print("✅ Test activity deleted")
                else:
                    print(f"⚠️  Could not delete test activity: {response.status_code}")
    
    async def run_test(self):
        """Run the complete notification test."""
        print("🚀 Starting Notification System Test")
        print("=" * 50)
        
        try:
            # Setup
            if not await self.setup_users():
                print("❌ Failed to setup users")
                return False
            
            if not await self.create_test_activity():
                print("❌ Failed to create test activity")
                return False
            
            if not await self.invite_users_to_activity():
                print("❌ Failed to invite users")
                return False
            
            # Get baseline notification count
            initial_count = await self.get_organizer_notifications_before()
            if initial_count is None:
                print("❌ Failed to get initial notification count")
                return False
            
            # Submit responses
            if not await self.submit_registered_user_response():
                print("❌ Failed to submit registered user response")
                return False
            
            if not await self.submit_guest_user_response():
                print("❌ Failed to submit guest user response")
                return False
            
            # Verify notifications
            if not await self.verify_organizer_notifications(initial_count):
                print("❌ Notification verification failed")
                return False
            
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Organizers now receive notifications for both registered and guest user responses")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main test function."""
    tester = NotificationTester()
    success = await tester.run_test()
    
    if success:
        print("\n🎯 NOTIFICATION SYSTEM FIX VERIFIED!")
        print("The issue has been resolved - organizers will now receive notifications")
        print("when invited users (both registered and guests) respond to activities.")
    else:
        print("\n❌ TEST FAILED!")
        print("The notification system may still have issues.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())