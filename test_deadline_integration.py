#!/usr/bin/env python3
"""
End-to-End Integration Test for Deadline Feature

This test demonstrates the complete deadline workflow:
1. Create activity with deadline
2. Send invitations
3. Simulate deadline approaching
4. Verify notifications are sent
5. Test frontend deadline display

Run with: python test_deadline_integration.py
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import httpx
    from motor.motor_asyncio import AsyncIOMotorClient
    from bson import ObjectId
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("Please install: pip install httpx motor")
    sys.exit(1)

# Configuration from .test-env
API_BASE_URL = "http://localhost:8000"
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "sunnyside_test"

# Test credentials from .test-env
TEST_EMAIL = "test@testy.com"
TEST_PASSWORD = "W^XXT$%L7hddx*GJSJEp"
TEST_USER_NAME = "Testy user"

class DeadlineIntegrationTest:
    """End-to-end integration test for deadline feature."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0)
        self.db_client = None
        self.db = None
        self.auth_token = None
        self.test_user_id = None
        self.activity_id = None
        
    async def setup(self):
        """Set up test environment."""
        print("🔧 Setting up integration test environment...")
        
        # Connect to MongoDB
        try:
            self.db_client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.db_client[DATABASE_NAME]
            await self.db.command("ping")
            print("✅ Connected to MongoDB")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
        
        # Authenticate
        success = await self.authenticate()
        if not success:
            return False
        
        print("✅ Integration test environment ready")
        return True
    
    async def authenticate(self):
        """Authenticate with test user."""
        try:
            login_data = {
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = await self.client.post("/api/v1/auth/login", json=login_data)
            if response.status_code != 200:
                print(f"❌ Failed to login: {response.text}")
                return False
            
            auth_data = response.json()
            self.auth_token = auth_data["access_token"]
            
            # Get user info
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get("/api/v1/auth/me", headers=headers)
            if response.status_code == 200:
                user_info = response.json()
                self.test_user_id = user_info["id"]
                print(f"✅ Authenticated as: {user_info['name']}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    async def step_1_create_activity_with_deadline(self) -> bool:
        """Step 1: Create an activity with a deadline."""
        print("\n📝 Step 1: Creating activity with deadline...")
        
        # Set deadline for 24 hours from now
        deadline = datetime.utcnow() + timedelta(hours=24)
        
        activity_data = {
            "title": "Integration Test - Weekend BBQ",
            "description": "Testing complete deadline workflow with a weekend barbecue",
            "timeframe": "Saturday afternoon",
            "activity_type": "food",
            "deadline": deadline.isoformat()
        }
        
        try:
            response = await self.client.post(
                "/api/v1/activities",
                json=activity_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to create activity: {response.text}")
                return False
            
            activity = response.json()
            self.activity_id = activity["id"]
            
            print(f"✅ Activity created: {activity['title']}")
            print(f"   Activity ID: {activity['id']}")
            print(f"   Deadline: {activity['deadline']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Exception in step 1: {e}")
            return False
    
    async def step_2_send_invitations(self) -> bool:
        """Step 2: Send invitations to test guests."""
        print("\n📧 Step 2: Sending invitations...")
        
        if not self.activity_id:
            print("❌ No activity ID available")
            return False
        
        invite_data = {
            "invitees": [
                {"name": "Alice Test", "email": "alice@test.deadline"},
                {"name": "Bob Test", "email": "bob@test.deadline"},
                {"name": "Charlie Test", "email": "charlie@test.deadline"}
            ],
            "custom_message": "Join us for a fun BBQ! Please respond by the deadline."
        }
        
        try:
            response = await self.client.post(
                f"/api/v1/activities/{self.activity_id}/invite",
                json=invite_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to send invitations: {response.text}")
                return False
            
            result = response.json()
            print(f"✅ Invitations sent to {result.get('invited_count', 0)} people")
            print(f"   Emails sent: {result.get('emails_sent', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Exception in step 2: {e}")
            return False
    
    async def step_3_simulate_deadline_approaching(self) -> bool:
        """Step 3: Simulate deadline approaching by updating the deadline."""
        print("\n⏰ Step 3: Simulating approaching deadline...")
        
        if not self.activity_id:
            print("❌ No activity ID available")
            return False
        
        try:
            # Update deadline to 2 hours from now (should trigger approaching deadline notification)
            approaching_deadline = datetime.utcnow() + timedelta(hours=2)
            
            update_data = {
                "deadline": approaching_deadline.isoformat()
            }
            
            response = await self.client.put(
                f"/api/v1/activities/{self.activity_id}",
                json=update_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to update deadline: {response.text}")
                return False
            
            activity = response.json()
            print(f"✅ Deadline updated to: {activity['deadline']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Exception in step 3: {e}")
            return False
    
    async def step_4_run_deadline_scheduler(self) -> bool:
        """Step 4: Run the deadline scheduler to trigger notifications."""
        print("\n🔔 Step 4: Running deadline scheduler...")
        
        try:
            from backend.services.deadline_scheduler import DeadlineScheduler
            
            scheduler = DeadlineScheduler()
            
            if self.db is None:
                print("❌ Database not available")
                return False
            
            # Run deadline check
            result = await scheduler.check_deadlines(self.db)
            
            if not result.get("success"):
                print(f"❌ Deadline scheduler failed: {result.get('error')}")
                return False
            
            print(f"✅ Deadline scheduler completed")
            print(f"   Activities checked: {result.get('activities_checked', 0)}")
            print(f"   Notifications sent: {result.get('notifications_sent', 0)}")
            print(f"   Emails sent: {result.get('emails_sent', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Exception in step 4: {e}")
            return False
    
    async def step_5_verify_notifications(self) -> bool:
        """Step 5: Verify that deadline notifications were created."""
        print("\n✅ Step 5: Verifying notifications...")
        
        try:
            # Get notifications via API
            response = await self.client.get(
                "/api/v1/notifications",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get notifications: {response.text}")
                return False
            
            notifications = response.json()
            
            # Filter deadline notifications
            deadline_notifications = [
                n for n in notifications 
                if n.get("notification_type", "").startswith("deadline")
            ]
            
            print(f"✅ Found {len(deadline_notifications)} deadline notifications")
            
            for notif in deadline_notifications:
                print(f"   - {notif['notification_type']}: {notif['message']}")
            
            return len(deadline_notifications) > 0
            
        except Exception as e:
            print(f"❌ Exception in step 5: {e}")
            return False
    
    async def step_6_test_activity_summary(self) -> bool:
        """Step 6: Test activity summary shows deadline information."""
        print("\n📊 Step 6: Testing activity summary with deadline...")
        
        if not self.activity_id:
            print("❌ No activity ID available")
            return False
        
        try:
            response = await self.client.get(
                f"/api/v1/activities/{self.activity_id}/summary",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get activity summary: {response.text}")
                return False
            
            summary = response.json()
            activity = summary.get("activity", {})
            summary_data = summary.get("summary", {})
            
            if not activity.get("deadline"):
                print("❌ Deadline not in activity summary")
                return False
            
            deadline_passed = summary_data.get("deadline_passed", False)
            
            print(f"✅ Activity summary includes deadline: {activity['deadline']}")
            print(f"   Deadline passed: {deadline_passed}")
            print(f"   Total invitees: {summary_data.get('total_invitees', 0)}")
            print(f"   Response rate: {summary_data.get('response_rate', 0)}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Exception in step 6: {e}")
            return False
    
    async def step_7_test_public_activity(self) -> bool:
        """Step 7: Test public activity endpoint includes deadline (for guests)."""
        print("\n🌐 Step 7: Testing public activity with deadline...")
        
        if not self.activity_id:
            print("❌ No activity ID available")
            return False
        
        try:
            # Test public activity endpoint (no auth required)
            response = await self.client.get(f"/api/v1/invites/{self.activity_id}")
            
            if response.status_code != 200:
                print(f"❌ Failed to get public activity: {response.text}")
                return False
            
            activity = response.json()
            
            if not activity.get("deadline"):
                print("❌ Deadline not in public activity")
                return False
            
            print(f"✅ Public activity includes deadline: {activity['deadline']}")
            print(f"   Title: {activity['title']}")
            print(f"   Organizer: {activity['organizer_name']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Exception in step 7: {e}")
            return False
    
    async def cleanup(self):
        """Clean up test data."""
        print("\n🧹 Cleaning up test data...")
        
        if self.db is not None:
            # Clean up test activities
            await self.db.activities.delete_many({
                "title": {"$regex": "Integration Test.*"}
            })
            # Clean up test notifications
            await self.db.notifications.delete_many({
                "notification_type": {"$in": ["deadline_reminder", "deadline_warning", "deadline_passed"]}
            })
            print("✅ Test data cleaned up")
    
    async def run_integration_test(self) -> bool:
        """Run the complete end-to-end integration test."""
        print("🚀 Starting Deadline Feature Integration Test")
        print("=" * 60)
        
        # Setup
        if not await self.setup():
            return False
        
        # Test steps
        steps = [
            ("Create Activity with Deadline", self.step_1_create_activity_with_deadline),
            ("Send Invitations", self.step_2_send_invitations),
            ("Simulate Approaching Deadline", self.step_3_simulate_deadline_approaching),
            ("Run Deadline Scheduler", self.step_4_run_deadline_scheduler),
            ("Verify Notifications", self.step_5_verify_notifications),
            ("Test Activity Summary", self.step_6_test_activity_summary),
            ("Test Public Activity", self.step_7_test_public_activity),
        ]
        
        passed = 0
        failed = 0
        
        for step_name, step_func in steps:
            try:
                print(f"\n{'='*20} {step_name} {'='*20}")
                result = await step_func()
                if result:
                    passed += 1
                    print(f"✅ {step_name} - PASSED")
                else:
                    failed += 1
                    print(f"❌ {step_name} - FAILED")
            except Exception as e:
                print(f"❌ {step_name} failed with exception: {e}")
                failed += 1
        
        # Cleanup
        await self.cleanup()
        
        # Results
        print("\n" + "=" * 60)
        print("🏁 Integration Test Complete")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed == 0:
            print("\n🎉 All integration tests passed! Deadline feature is working end-to-end.")
        else:
            print(f"\n⚠️ {failed} integration test(s) failed. Please check the implementation.")
        
        return failed == 0
    
    async def close(self):
        """Clean up resources."""
        if self.client:
            await self.client.aclose()
        if self.db_client:
            self.db_client.close()

async def main():
    """Main integration test runner."""
    test_suite = DeadlineIntegrationTest()
    
    try:
        success = await test_suite.run_integration_test()
        return 0 if success else 1
    finally:
        await test_suite.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)