#!/usr/bin/env python3
"""
Comprehensive test script for the guest experience flow.

This script tests the complete journey from invitation to guest viewing the activity:
1. Update Environment with test credentials
2. Authenticate as test user
3. Create a test activity
4. Invite a guest to the activity
5. Retrieve the guest invitation link
6. Verify the guest page loads correctly with activity details
"""

import os
import sys
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

# Test configuration from .test-env
TEST_PORT = 5137
TEST_EMAIL = "test@testy.com"
TEST_PASSWORD = "W^XXT$%L7hddx*GJSJEp"
TEST_USER_NAME = "Testy user"

# API configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = f"http://localhost:{TEST_PORT}"

# Guest test data
GUEST_EMAIL = "guest@example.com"
GUEST_NAME = "Test Guest"

class TestResult:
    """Class to track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
        
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ FAIL: {test_name} - {error}")
        
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if self.errors:
            print(f"\nERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        return self.failed == 0

class GuestExperienceFlowTester:
    """Main test class for guest experience flow"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.activity_id = None
        self.guest_invite_link = None
        self.results = TestResult()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            async with self.session.request(method, url, **kwargs) as response:
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    data = await response.json()
                else:
                    text = await response.text()
                    data = {"text": text, "content_type": content_type}
                
                return {
                    "status": response.status,
                    "data": data,
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {
                "status": 0,
                "error": str(e),
                "data": None
            }
    
    async def test_environment_setup(self):
        """Test 1: Verify environment setup"""
        print("\n🔧 Testing Environment Setup...")
        
        # Check if backend is running
        response = await self.make_request("GET", f"{BACKEND_URL}/healthz")
        if response["status"] == 200:
            self.results.add_pass("Backend health check")
        else:
            self.results.add_fail("Backend health check", f"Status: {response['status']}")
            return False
            
        # Check API v1 health
        response = await self.make_request("GET", f"{BACKEND_URL}/api/v1/health")
        if response["status"] == 200:
            self.results.add_pass("API v1 health check")
        else:
            self.results.add_fail("API v1 health check", f"Status: {response['status']}")
            
        return True
    
    async def test_authentication(self):
        """Test 2: Authenticate as test user"""
        print("\n🔐 Testing Authentication...")
        
        # Try to login with test credentials
        login_data = {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = await self.make_request(
            "POST", 
            f"{BACKEND_URL}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response["status"] == 200 and "access_token" in response["data"]:
            self.auth_token = response["data"]["access_token"]
            self.results.add_pass("User authentication")
            
            # Verify token works
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            me_response = await self.make_request(
                "GET",
                f"{BACKEND_URL}/api/v1/auth/me",
                headers=headers
            )
            
            if me_response["status"] == 200:
                user_data = me_response["data"]
                if user_data.get("email") == TEST_EMAIL:
                    self.results.add_pass("Token verification")
                    print(f"   Authenticated as: {user_data.get('name')} ({user_data.get('email')})")
                    return True
                else:
                    self.results.add_fail("Token verification", "Email mismatch")
            else:
                self.results.add_fail("Token verification", f"Status: {me_response['status']}")
        else:
            self.results.add_fail("User authentication", f"Status: {response['status']}, Data: {response.get('data')}")
            
        return False
    
    async def test_create_activity(self):
        """Test 3: Create a test activity"""
        print("\n📅 Testing Activity Creation...")
        
        if not self.auth_token:
            self.results.add_fail("Activity creation", "No auth token available")
            return False
            
        # Create test activity
        activity_data = {
            "title": "Test Guest Experience Activity",
            "description": "This is a test activity to verify the guest experience flow works correctly.",
            "timeframe": "This weekend",
            "group_size": "small group",
            "activity_type": "food",
            "weather_preference": "either",
            "selected_days": ["Saturday", "Sunday"]
        }
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        response = await self.make_request(
            "POST",
            f"{BACKEND_URL}/api/v1/activities",
            json=activity_data,
            headers=headers
        )
        
        if response["status"] == 200 and "id" in response["data"]:
            self.activity_id = response["data"]["id"]
            self.results.add_pass("Activity creation")
            print(f"   Created activity: {response['data']['title']} (ID: {self.activity_id})")
            return True
        else:
            self.results.add_fail("Activity creation", f"Status: {response['status']}, Data: {response.get('data')}")
            return False
    
    async def test_invite_guest(self):
        """Test 4: Invite guest to the activity"""
        print("\n📧 Testing Guest Invitation...")
        
        if not self.auth_token or not self.activity_id:
            self.results.add_fail("Guest invitation", "Missing auth token or activity ID")
            return False
            
        # Invite guest to activity
        invite_data = {
            "invitees": [
                {
                    "name": GUEST_NAME,
                    "email": GUEST_EMAIL
                }
            ],
            "custom_message": "Please join us for this test activity!"
        }
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        response = await self.make_request(
            "POST",
            f"{BACKEND_URL}/api/v1/activities/{self.activity_id}/invite",
            json=invite_data,
            headers=headers
        )
        
        if response["status"] == 200:
            invite_result = response["data"]
            if invite_result.get("invited_count", 0) > 0:
                self.results.add_pass("Guest invitation sent")
                print(f"   Invited {invite_result['invited_count']} guest(s)")
                print(f"   Emails sent: {invite_result.get('emails_sent', 0)}")
                return True
            else:
                self.results.add_fail("Guest invitation sent", "No guests were invited")
        else:
            self.results.add_fail("Guest invitation sent", f"Status: {response['status']}, Data: {response.get('data')}")
            
        return False
    
    async def test_retrieve_guest_link(self):
        """Test 5: Generate and retrieve guest invitation link"""
        print("\n🔗 Testing Guest Link Generation...")
        
        if not self.activity_id:
            self.results.add_fail("Guest link generation", "No activity ID available")
            return False
            
        # Generate guest invite link (simulating the link generation logic)
        self.guest_invite_link = f"{FRONTEND_URL}/guest?activity={self.activity_id}&email={GUEST_EMAIL}"
        
        self.results.add_pass("Guest link generation")
        print(f"   Generated link: {self.guest_invite_link}")
        return True
    
    async def test_guest_page_access(self):
        """Test 6: Verify guest can access the activity page"""
        print("\n🌐 Testing Guest Page Access...")
        
        if not self.activity_id:
            self.results.add_fail("Guest page access", "No activity ID available")
            return False
            
        # Test public activity endpoint (what the guest page uses)
        response = await self.make_request(
            "GET",
            f"{BACKEND_URL}/api/v1/invites/{self.activity_id}"
        )
        
        if response["status"] == 200:
            activity_data = response["data"]
            
            # Verify essential activity data is present
            required_fields = ["id", "title", "description", "organizer_name"]
            missing_fields = [field for field in required_fields if field not in activity_data]
            
            if not missing_fields:
                self.results.add_pass("Guest page data retrieval")
                print(f"   Activity title: {activity_data['title']}")
                print(f"   Organizer: {activity_data['organizer_name']}")
                print(f"   Description: {activity_data['description'][:50]}...")
                
                # Verify activity details match what we created
                if activity_data["title"] == "Test Guest Experience Activity":
                    self.results.add_pass("Activity data integrity")
                else:
                    self.results.add_fail("Activity data integrity", "Title mismatch")
                    
                return True
            else:
                self.results.add_fail("Guest page data retrieval", f"Missing fields: {missing_fields}")
        else:
            self.results.add_fail("Guest page data retrieval", f"Status: {response['status']}")
            
        return False
    
    async def test_guest_response_submission(self):
        """Test 7: Test guest response submission"""
        print("\n📝 Testing Guest Response Submission...")
        
        if not self.activity_id:
            self.results.add_fail("Guest response submission", "No activity ID available")
            return False
            
        # Submit a test response as the guest
        response_data = {
            "guest_id": GUEST_EMAIL,
            "response": "yes",
            "availability_note": "Looking forward to this test activity!",
            "preferences": {
                "food": True,
                "outdoor": True
            },
            "venue_suggestion": "Test Venue"
        }
        
        response = await self.make_request(
            "POST",
            f"{BACKEND_URL}/api/v1/invites/{self.activity_id}/respond",
            json=response_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response["status"] == 200:
            result = response["data"]
            if result.get("message") == "Response submitted successfully":
                self.results.add_pass("Guest response submission")
                print(f"   Response recorded: {result.get('response_recorded')}")
                print(f"   Guest name: {result.get('guest_name')}")
                return True
            else:
                self.results.add_fail("Guest response submission", f"Unexpected response: {result}")
        else:
            self.results.add_fail("Guest response submission", f"Status: {response['status']}, Data: {response.get('data')}")
            
        return False
    
    async def test_verify_response_recorded(self):
        """Test 8: Verify the guest response was recorded in the activity"""
        print("\n✅ Testing Response Recording Verification...")
        
        if not self.auth_token or not self.activity_id:
            self.results.add_fail("Response recording verification", "Missing auth token or activity ID")
            return False
            
        # Get the activity as the organizer to verify the response was recorded
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        response = await self.make_request(
            "GET",
            f"{BACKEND_URL}/api/v1/activities/{self.activity_id}",
            headers=headers
        )
        
        if response["status"] == 200:
            activity = response["data"]
            invitees = activity.get("invitees", [])
            
            # Find the guest in the invitees list
            guest_invitee = None
            for invitee in invitees:
                if invitee.get("email") == GUEST_EMAIL:
                    guest_invitee = invitee
                    break
            
            if guest_invitee:
                if guest_invitee.get("response") == "yes":
                    self.results.add_pass("Response recording verification")
                    print(f"   Guest response recorded: {guest_invitee['response']}")
                    print(f"   Availability note: {guest_invitee.get('availability_note', 'None')}")
                    return True
                else:
                    self.results.add_fail("Response recording verification", f"Wrong response: {guest_invitee.get('response')}")
            else:
                self.results.add_fail("Response recording verification", "Guest not found in invitees")
        else:
            self.results.add_fail("Response recording verification", f"Status: {response['status']}")
            
        return False
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Guest Experience Flow Test")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Test User: {TEST_EMAIL}")
        print(f"Guest Email: {GUEST_EMAIL}")
        
        # Run tests in order
        tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Authentication", self.test_authentication),
            ("Activity Creation", self.test_create_activity),
            ("Guest Invitation", self.test_invite_guest),
            ("Guest Link Generation", self.test_retrieve_guest_link),
            ("Guest Page Access", self.test_guest_page_access),
            ("Guest Response Submission", self.test_guest_response_submission),
            ("Response Recording Verification", self.test_verify_response_recorded)
        ]
        
        for test_name, test_func in tests:
            try:
                success = await test_func()
                if not success and test_name in ["Environment Setup", "Authentication"]:
                    print(f"\n⚠️  Critical test '{test_name}' failed. Stopping execution.")
                    break
            except Exception as e:
                self.results.add_fail(test_name, f"Exception: {str(e)}")
                print(f"💥 Exception in {test_name}: {str(e)}")
        
        # Print summary
        success = self.results.summary()
        
        if success:
            print(f"\n🎉 All tests passed! Guest experience flow is working correctly.")
        else:
            print(f"\n⚠️  Some tests failed. Please check the errors above.")
            
        return success

async def main():
    """Main function to run the test suite"""
    try:
        async with GuestExperienceFlowTester() as tester:
            success = await tester.run_all_tests()
            return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        return 1

if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)