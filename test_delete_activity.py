#!/usr/bin/env python3
"""
Test script for the DELETE activity endpoint.
This script tests various scenarios for deleting activities.
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

async def test_delete_activity():
    """Test the delete activity functionality."""
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing DELETE activity endpoint...")
        
        # Step 1: Login to get auth token
        print("\n1. Logging in...")
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        async with session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
            if response.status != 200:
                print(f"❌ Login failed with status {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
                return
            
            login_result = await response.json()
            token = login_result.get("access_token")
            if not token:
                print("❌ No access token received")
                return
            
            print("✅ Login successful")
        
        # Headers for authenticated requests
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Create a test activity
        print("\n2. Creating test activity...")
        activity_data = {
            "title": "Test Activity for Deletion",
            "description": "This activity will be deleted as part of testing",
            "timeframe": "next weekend",
            "groupSize": "small group",
            "activityType": "outdoor",
            "weatherPreference": "sunny",
            "selectedDate": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        async with session.post(f"{BASE_URL}/activities", json=activity_data, headers=headers) as response:
            if response.status != 200:
                print(f"❌ Activity creation failed with status {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
                return
            
            activity = await response.json()
            activity_id = activity.get("id")
            if not activity_id:
                print("❌ No activity ID received")
                return
            
            print(f"✅ Activity created with ID: {activity_id}")
        
        # Step 3: Test deleting the activity (should be simple deletion - no invites sent)
        print(f"\n3. Deleting activity {activity_id}...")
        
        async with session.delete(f"{BASE_URL}/activities/{activity_id}", headers=headers) as response:
            if response.status != 200:
                print(f"❌ Activity deletion failed with status {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
                return
            
            delete_result = await response.json()
            print("✅ Activity deleted successfully")
            print(f"Delete result: {json.dumps(delete_result, indent=2)}")
        
        # Step 4: Verify activity is deleted by trying to fetch it
        print(f"\n4. Verifying activity {activity_id} is deleted...")
        
        async with session.get(f"{BASE_URL}/activities/{activity_id}", headers=headers) as response:
            if response.status == 404:
                print("✅ Activity confirmed deleted (404 Not Found)")
            else:
                print(f"❌ Activity still exists (status: {response.status})")
                response_text = await response.text()
                print(f"Response: {response_text}")
        
        # Step 5: Create another activity and send invites, then delete
        print("\n5. Creating activity with invites for advanced deletion test...")
        
        activity_data_with_invites = {
            "title": "Test Activity with Invites",
            "description": "This activity will have invites and then be deleted",
            "timeframe": "next weekend",
            "groupSize": "small group",
            "activityType": "outdoor",
            "weatherPreference": "sunny",
            "selectedDate": (datetime.utcnow() + timedelta(days=10)).isoformat()
        }
        
        async with session.post(f"{BASE_URL}/activities", json=activity_data_with_invites, headers=headers) as response:
            if response.status != 200:
                print(f"❌ Second activity creation failed with status {response.status}")
                return
            
            activity2 = await response.json()
            activity2_id = activity2.get("id")
            print(f"✅ Second activity created with ID: {activity2_id}")
        
        # Step 6: Send invites to the activity
        print(f"\n6. Sending invites to activity {activity2_id}...")
        
        invite_data = {
            "invitees": [
                {"name": "Test User 1", "email": "testuser1@example.com"},
                {"name": "Test User 2", "email": "testuser2@example.com"}
            ],
            "custom_message": "Join us for this test activity!"
        }
        
        async with session.post(f"{BASE_URL}/activities/{activity2_id}/invite", json=invite_data, headers=headers) as response:
            if response.status != 200:
                print(f"❌ Invite sending failed with status {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
            else:
                invite_result = await response.json()
                print("✅ Invites sent successfully")
                print(f"Invite result: {json.dumps(invite_result, indent=2)}")
        
        # Step 7: Delete the activity with invites (should trigger notifications)
        print(f"\n7. Deleting activity with invites {activity2_id}...")
        
        async with session.delete(f"{BASE_URL}/activities/{activity2_id}", headers=headers) as response:
            if response.status != 200:
                print(f"❌ Activity with invites deletion failed with status {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
                return
            
            delete_result2 = await response.json()
            print("✅ Activity with invites deleted successfully")
            print(f"Delete result: {json.dumps(delete_result2, indent=2)}")
            
            # Check if notifications were sent
            if delete_result2.get("notifications_sent"):
                print(f"✅ Cancellation notifications sent to {delete_result2.get('invitees_notified', 0)} invitees")
                print(f"✅ {delete_result2.get('emails_sent', 0)} emails sent successfully")
            else:
                print("ℹ️ No notifications sent (expected for draft activities)")
        
        # Step 8: Test unauthorized deletion (try to delete non-existent activity)
        print("\n8. Testing unauthorized deletion...")
        fake_activity_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format but non-existent
        
        async with session.delete(f"{BASE_URL}/activities/{fake_activity_id}", headers=headers) as response:
            if response.status == 404:
                print("✅ Correctly returned 404 for non-existent activity")
            else:
                print(f"❌ Unexpected status {response.status} for non-existent activity")
        
        print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_delete_activity())