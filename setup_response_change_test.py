#!/usr/bin/env python3
"""
Setup script to create a test scenario for response change modal testing.
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

# Test configuration
BACKEND_URL = "http://localhost:8000"
TEST_EMAIL = "test@testy.com"
TEST_PASSWORD = "W^XXT$%L7hddx*GJSJEp"
TEST_USER_NAME = "Testy user"

async def setup_test_scenario():
    """Setup test scenario with existing response"""
    client = httpx.AsyncClient()
    
    try:
        print("🚀 Setting up response change test scenario...")
        
        # Authenticate
        login_data = {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = await client.post(f"{BACKEND_URL}/api/v1/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
            
        data = response.json()
        auth_token = data["access_token"]
        print("✅ Authenticated successfully")
        
        # Create test activity
        headers = {"Authorization": f"Bearer {auth_token}"}
        activity_data = {
            "title": "Frontend Response Change Test",
            "description": "Testing frontend response change modal",
            "timeframe": "evening",
            "group_size": "small group",
            "activity_type": "food",
            "weather_preference": "either",
            "selected_days": ["Saturday", "Sunday"],
            "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        response = await client.post(f"{BACKEND_URL}/api/v1/activities", json=activity_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to create activity: {response.status_code}")
            return None
            
        data = response.json()
        activity_id = data["id"]
        print(f"✅ Test activity created: {activity_id}")
        
        # Invite the test user
        invite_data = {
            "invitees": [
                {"name": TEST_USER_NAME, "email": TEST_EMAIL}
            ],
            "custom_message": "Please join our test activity!"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/api/v1/activities/{activity_id}/invite", 
            json=invite_data, 
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to send invitations: {response.status_code}")
            return None
            
        print("✅ Invitation sent")
        
        # Submit initial response
        response_data = {
            "response": "yes",
            "availabilityNote": "I'm available and excited!",
            "preferences": {"food": True, "outdoor": True},
            "venueSuggestion": "Local park cafe"
        }
        
        response = await client.post(
            f"{BACKEND_URL}/api/v1/activities/{activity_id}/respond", 
            json=response_data, 
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to submit initial response: {response.status_code}")
            return None
            
        print("✅ Initial response 'yes' submitted")
        
        print(f"""
🎯 Test scenario ready!
   Activity ID: {activity_id}
   Initial Response: YES
   
   Now you can:
   1. Go to http://localhost:5137
   2. Login with {TEST_EMAIL}
   3. Go to the 'Invited' tab
   4. Click on 'Frontend Response Change Test'
   5. Try changing the response to test the modal
        """)
        
        return activity_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(setup_test_scenario())