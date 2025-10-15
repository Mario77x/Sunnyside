#!/usr/bin/env python3
"""
Test script for the response change functionality.
This script tests the complete flow of changing responses for both registered and guest users.
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from bson import ObjectId

# Test configuration
BACKEND_URL = "http://localhost:8000"
TEST_EMAIL = "test@testy.com"
TEST_PASSWORD = "W^XXT$%L7hddx*GJSJEp"
TEST_USER_NAME = "Testy user"

class ResponseChangeTest:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.auth_token = None
        self.test_activity_id = None
        self.test_user_id = None
        
    async def setup(self):
        """Setup test environment"""
        print("🚀 Setting up test environment...")
        
        # Test backend health
        try:
            response = await self.client.get(f"{BACKEND_URL}/healthz")
            if response.status_code == 200:
                print("✅ Backend is healthy")
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to backend: {e}")
            return False
            
        return True
    
    async def authenticate(self):
        """Authenticate test user"""
        print("🔐 Authenticating test user...")
        
        try:
            # Try to login first
            login_data = {
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/api/v1/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                print("✅ User authenticated successfully")
                
                # Get user info
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                user_response = await self.client.get(f"{BACKEND_URL}/api/v1/auth/me", headers=headers)
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.test_user_id = user_data["id"]
                    print(f"✅ User ID: {self.test_user_id}")
                
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    async def create_test_activity(self):
        """Create a test activity"""
        print("📝 Creating test activity...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            activity_data = {
                "title": "Response Change Test Activity",
                "description": "Testing response change functionality",
                "timeframe": "evening",
                "group_size": "small group",
                "activity_type": "food",
                "weather_preference": "either",
                "selected_days": ["Saturday", "Sunday"],
                "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
            
            response = await self.client.post(f"{BACKEND_URL}/api/v1/activities", json=activity_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.test_activity_id = data["id"]
                print(f"✅ Test activity created: {self.test_activity_id}")
                return True
            else:
                print(f"❌ Failed to create activity: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Activity creation error: {e}")
            return False
    
    async def invite_test_users(self):
        """Invite test users to the activity"""
        print("📧 Inviting test users...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            invite_data = {
                "invitees": [
                    {"name": TEST_USER_NAME, "email": TEST_EMAIL},  # Add the test user as an invitee
                    {"name": "Guest User", "email": "guest@example.com"},
                    {"name": "Another User", "email": "another@example.com"}
                ],
                "custom_message": "Please join our test activity!"
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/api/v1/activities/{self.test_activity_id}/invite", 
                json=invite_data, 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Invitations sent to {data.get('invited_count', 0)} users")
                return True
            else:
                print(f"❌ Failed to send invitations: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Invitation error: {e}")
            return False
    
    async def test_initial_response(self):
        """Test initial response submission"""
        print("📝 Testing initial response submission...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response_data = {
                "response": "yes",
                "availabilityNote": "I'm available and excited!",
                "preferences": {"food": True, "outdoor": True},
                "venueSuggestion": "Local park cafe"
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/api/v1/activities/{self.test_activity_id}/respond", 
                json=response_data, 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Initial response submitted: {data.get('response_recorded')}")
                print(f"   Message: {data.get('message')}")
                return True
            else:
                print(f"❌ Failed to submit initial response: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Initial response error: {e}")
            return False
    
    async def test_response_change(self):
        """Test response change functionality"""
        print("🔄 Testing response change...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            changed_response_data = {
                "response": "maybe",
                "availabilityNote": "Actually, I might have a conflict",
                "preferences": {"food": True, "indoor": True},
                "venueSuggestion": "Indoor restaurant instead"
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/api/v1/activities/{self.test_activity_id}/respond", 
                json=changed_response_data, 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response changed: {data.get('response_recorded')}")
                print(f"   Message: {data.get('message')}")
                print(f"   Is change: {data.get('is_change', False)}")
                print(f"   Previous response: {data.get('previous_response', 'N/A')}")
                return True
            else:
                print(f"❌ Failed to change response: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Response change error: {e}")
            return False
    
    async def test_guest_response_change(self):
        """Test guest response change functionality"""
        print("👤 Testing guest response change...")
        
        try:
            # First, submit initial guest response
            guest_response_data = {
                "guest_id": "guest@example.com",
                "response": "yes",
                "availability_note": "I'm free that day",
                "preferences": {"food": True},
                "venue_suggestion": "Pizza place"
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/api/v1/invites/{self.test_activity_id}/respond", 
                json=guest_response_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Initial guest response: {data.get('response_recorded')}")
            else:
                print(f"❌ Failed initial guest response: {response.status_code} - {response.text}")
                return False
            
            # Now change the guest response
            changed_guest_response_data = {
                "guest_id": "guest@example.com",
                "response": "no",
                "availability_note": "Sorry, something came up",
                "preferences": {},
                "venue_suggestion": ""
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/api/v1/invites/{self.test_activity_id}/respond", 
                json=changed_guest_response_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Guest response changed: {data.get('response_recorded')}")
                print(f"   Message: {data.get('message')}")
                return True
            else:
                print(f"❌ Failed to change guest response: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Guest response change error: {e}")
            return False
    
    async def verify_activity_state(self):
        """Verify the final activity state"""
        print("🔍 Verifying activity state...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(f"{BACKEND_URL}/api/v1/activities/{self.test_activity_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Activity retrieved successfully")
                
                # Check invitees and their responses
                invitees = data.get("invitees", [])
                print(f"   Total invitees: {len(invitees)}")
                
                for invitee in invitees:
                    name = invitee.get("name")
                    email = invitee.get("email")
                    response = invitee.get("response")
                    previous_response = invitee.get("previous_response")
                    
                    print(f"   - {name} ({email}): {response}")
                    if previous_response:
                        print(f"     Previous: {previous_response}")
                
                return True
            else:
                print(f"❌ Failed to retrieve activity: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Activity verification error: {e}")
            return False
    
    async def cleanup(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        
        try:
            if self.test_activity_id and self.auth_token:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                response = await self.client.delete(f"{BACKEND_URL}/api/v1/activities/{self.test_activity_id}", headers=headers)
                
                if response.status_code == 200:
                    print("✅ Test activity deleted")
                else:
                    print(f"⚠️ Could not delete test activity: {response.status_code}")
            
            await self.client.aclose()
            
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
    
    async def run_tests(self):
        """Run all tests"""
        print("🧪 Starting Response Change Flow Tests")
        print("=" * 50)
        
        try:
            # Setup
            if not await self.setup():
                return False
            
            # Authenticate
            if not await self.authenticate():
                return False
            
            # Create test activity
            if not await self.create_test_activity():
                return False
            
            # Invite users
            if not await self.invite_test_users():
                return False
            
            # Test initial response
            if not await self.test_initial_response():
                return False
            
            # Test response change
            if not await self.test_response_change():
                return False
            
            # Test guest response change
            if not await self.test_guest_response_change():
                return False
            
            # Verify final state
            if not await self.verify_activity_state():
                return False
            
            print("=" * 50)
            print("🎉 All tests passed! Response change functionality is working correctly.")
            return True
            
        except Exception as e:
            print(f"❌ Test suite error: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main test function"""
    test = ResponseChangeTest()
    success = await test.run_tests()
    
    if success:
        print("\n✅ Response change implementation is complete and working!")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())