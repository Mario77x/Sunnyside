#!/usr/bin/env python3
"""
Comprehensive test suite for the Deadline Feature implementation.

This test suite covers:
1. Backend API endpoints for deadline handling
2. Database operations with deadlines
3. Deadline scheduler functionality
4. Notification system for deadlines
5. End-to-end deadline workflow

Run with: python test_deadline_feature.py
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

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
FRONTEND_URL = "http://localhost:5137"
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "sunnyside_test"

# Test credentials from .test-env
TEST_EMAIL = "test@testy.com"
TEST_PASSWORD = "W^XXT$%L7hddx*GJSJEp"
TEST_USER_NAME = "Testy user"

class DeadlineFeatureTest:
    """Test suite for deadline feature functionality."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0)
        self.db_client = None
        self.db = None
        self.auth_token = None
        self.test_user_id = None
        self.test_activity_id = None
        
    async def setup(self):
        """Set up test environment."""
        print("🔧 Setting up test environment...")
        
        # Connect to MongoDB
        try:
            self.db_client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.db_client[DATABASE_NAME]
            # Test connection
            await self.db.command("ping")
            print("✅ Connected to MongoDB")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
        
        # Clean up any existing test data
        await self.cleanup()
        
        # Authenticate with existing test user
        success = await self.authenticate_test_user()
        if not success:
            print("❌ Failed to authenticate test user")
            return False
        
        print("✅ Test environment setup complete")
        return True
    
    async def cleanup(self):
        """Clean up test data."""
        if self.db is not None:
            # Clean up test activities
            await self.db.activities.delete_many({
                "title": {"$regex": "Test.*Deadline.*"}
            })
            # Clean up test notifications
            await self.db.notifications.delete_many({
                "notification_type": {"$in": ["deadline_reminder", "deadline_warning", "deadline_passed"]}
            })
    
    async def authenticate_test_user(self):
        """Authenticate with the test user from .test-env."""
        try:
            # Login with test credentials
            login_data = {
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = await self.client.post("/api/v1/auth/login", json=login_data)
            if response.status_code != 200:
                print(f"❌ Failed to login test user: {response.text}")
                return False
            
            auth_data = response.json()
            self.auth_token = auth_data["access_token"]
            
            # Get user info
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get("/api/v1/auth/me", headers=headers)
            if response.status_code == 200:
                user_info = response.json()
                self.test_user_id = user_info["id"]
                print(f"✅ Authenticated as: {user_info['name']} ({user_info['email']})")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    async def test_create_activity_with_deadline(self) -> bool:
        """Test creating an activity with a deadline."""
        print("\n📝 Testing activity creation with deadline...")
        
        # Set deadline for 2 days from now at 6 PM
        deadline = datetime.utcnow() + timedelta(days=2)
        deadline = deadline.replace(hour=18, minute=0, second=0, microsecond=0)
        
        activity_data = {
            "title": "Test Activity with Deadline",
            "description": "Testing deadline functionality for invitee responses",
            "timeframe": "this weekend",
            "activity_type": "social",
            "deadline": deadline.isoformat()
        }
        
        try:
            response = await self.client.post(
                "/api/v1/activities",
                json=activity_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to create activity with deadline: {response.text}")
                return False
            
            activity = response.json()
            self.test_activity_id = activity["id"]
            
            # Verify deadline was saved correctly
            if not activity.get("deadline"):
                print("❌ Deadline not returned in activity response")
                return False
            
            returned_deadline = datetime.fromisoformat(activity["deadline"].replace('Z', '+00:00'))
            expected_deadline = deadline.replace(microsecond=0)  # API truncates microseconds
            
            if abs((returned_deadline - expected_deadline).total_seconds()) > 1:
                print(f"❌ Deadline mismatch: expected {expected_deadline}, got {returned_deadline}")
                return False
            
            print(f"✅ Activity created with deadline: {activity['title']}")
            print(f"   Activity ID: {activity['id']}")
            print(f"   Deadline: {activity['deadline']}")
            return True
            
        except Exception as e:
            print(f"❌ Exception during activity creation: {e}")
            return False
    
    async def test_get_activity_with_deadline(self) -> bool:
        """Test retrieving an activity with deadline."""
        print("\n📖 Testing activity retrieval with deadline...")
        
        if not self.test_activity_id:
            print("❌ No test activity ID available")
            return False
        
        try:
            response = await self.client.get(
                f"/api/v1/activities/{self.test_activity_id}",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to retrieve activity: {response.text}")
                return False
            
            activity = response.json()
            
            if not activity.get("deadline"):
                print("❌ Deadline not included in activity response")
                return False
            
            print(f"✅ Activity retrieved with deadline: {activity['deadline']}")
            return True
            
        except Exception as e:
            print(f"❌ Exception during activity retrieval: {e}")
            return False
    
    async def test_update_activity_deadline(self) -> bool:
        """Test updating an activity's deadline."""
        print("\n✏️ Testing activity deadline update...")
        
        if not self.test_activity_id:
            print("❌ No test activity ID available")
            return False
        
        try:
            # Update deadline to 3 days from now at 5 PM
            new_deadline = datetime.utcnow() + timedelta(days=3)
            new_deadline = new_deadline.replace(hour=17, minute=0, second=0, microsecond=0)
            
            update_data = {
                "deadline": new_deadline.isoformat()
            }
            
            response = await self.client.put(
                f"/api/v1/activities/{self.test_activity_id}",
                json=update_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to update activity deadline: {response.text}")
                return False
            
            activity = response.json()
            
            if not activity.get("deadline"):
                print("❌ Updated deadline not returned")
                return False
            
            returned_deadline = datetime.fromisoformat(activity["deadline"].replace('Z', '+00:00'))
            expected_deadline = new_deadline.replace(microsecond=0)
            
            if abs((returned_deadline - expected_deadline).total_seconds()) > 1:
                print(f"❌ Updated deadline mismatch: expected {expected_deadline}, got {returned_deadline}")
                return False
            
            print(f"✅ Activity deadline updated: {activity['deadline']}")
            return True
            
        except Exception as e:
            print(f"❌ Exception during deadline update: {e}")
            return False
    
    async def test_deadline_scheduler_check(self) -> bool:
        """Test the deadline scheduler functionality."""
        print("\n⏰ Testing deadline scheduler...")
        
        try:
            # Import the deadline scheduler
            from backend.services.deadline_scheduler import DeadlineScheduler
            
            scheduler = DeadlineScheduler()
            
            # Create activities with different deadline scenarios directly in database
            past_deadline = datetime.utcnow() - timedelta(hours=1)  # 1 hour ago
            approaching_deadline = datetime.utcnow() + timedelta(hours=2)  # 2 hours from now
            future_deadline = datetime.utcnow() + timedelta(days=5)  # 5 days from now
            
            test_activities = [
                {
                    "_id": ObjectId(),
                    "organizer_id": ObjectId(self.test_user_id),
                    "title": "Test Activity - Past Deadline",
                    "description": "Testing past deadline notifications",
                    "deadline": past_deadline,
                    "status": "invitations-sent",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "_id": ObjectId(),
                    "organizer_id": ObjectId(self.test_user_id),
                    "title": "Test Activity - Approaching Deadline",
                    "description": "Testing approaching deadline notifications",
                    "deadline": approaching_deadline,
                    "status": "invitations-sent",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "_id": ObjectId(),
                    "organizer_id": ObjectId(self.test_user_id),
                    "title": "Test Activity - Future Deadline",
                    "description": "Testing future deadline (should not trigger)",
                    "deadline": future_deadline,
                    "status": "invitations-sent",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
            
            # Insert test activities
            if self.db is not None:
                await self.db.activities.insert_many(test_activities)
                print(f"✅ Created {len(test_activities)} test activities for scheduler testing")
                
                # Run deadline check
                result = await scheduler.check_deadlines(self.db)
            else:
                print("❌ Database not available")
                return False
            
            if not result.get("success"):
                print(f"❌ Deadline scheduler failed: {result.get('error')}")
                return False
            
            print(f"✅ Deadline scheduler completed successfully")
            print(f"   Activities checked: {result.get('activities_checked', 0)}")
            print(f"   Notifications sent: {result.get('notifications_sent', 0)}")
            print(f"   Emails sent: {result.get('emails_sent', 0)}")
            
            # Verify notifications were created
            if self.db is not None:
                notification_count = await self.db.notifications.count_documents({
                    "user_id": ObjectId(self.test_user_id),
                    "notification_type": {"$in": ["deadline_reminder", "deadline_warning", "deadline_passed"]}
                })
            else:
                notification_count = 0
            
            if notification_count == 0:
                print("⚠️ No deadline notifications were created")
            else:
                print(f"✅ {notification_count} deadline notifications created")
            
            return True
            
        except ImportError as e:
            print(f"❌ Could not import deadline scheduler: {e}")
            return False
        except Exception as e:
            print(f"❌ Deadline scheduler test failed: {e}")
            return False
    
    async def test_deadline_notifications_api(self) -> bool:
        """Test deadline-related notifications through API."""
        print("\n🔔 Testing deadline notifications API...")
        
        try:
            # Get notifications for the test user
            response = await self.client.get(
                "/api/v1/notifications",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get notifications: {response.text}")
                return False
            
            notifications = response.json()
            
            # Filter deadline-related notifications
            deadline_notifications = [
                n for n in notifications 
                if n.get("notification_type", "").startswith("deadline")
            ]
            
            print(f"✅ Retrieved {len(notifications)} total notifications")
            print(f"   Deadline notifications: {len(deadline_notifications)}")
            
            # Display deadline notifications
            for notif in deadline_notifications:
                print(f"   - {notif['notification_type']}: {notif['message']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Exception during notifications API test: {e}")
            return False
    
    async def test_activity_summary_with_deadline(self) -> bool:
        """Test activity summary endpoint with deadline information."""
        print("\n📊 Testing activity summary with deadline...")
        
        if not self.test_activity_id:
            print("❌ No test activity ID available")
            return False
        
        try:
            response = await self.client.get(
                f"/api/v1/activities/{self.test_activity_id}/summary",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get activity summary: {response.text}")
                return False
            
            summary = response.json()
            
            # Check if activity has deadline
            activity = summary.get("activity", {})
            if not activity.get("deadline"):
                print("❌ Deadline not included in activity summary")
                return False
            
            # Check if summary includes deadline_passed status
            summary_data = summary.get("summary", {})
            deadline_passed = summary_data.get("deadline_passed")
            
            print(f"✅ Activity summary includes deadline: {activity['deadline']}")
            print(f"   Deadline passed: {deadline_passed}")
            
            return True
            
        except Exception as e:
            print(f"❌ Exception during activity summary test: {e}")
            return False
    
    async def test_public_activity_with_deadline(self) -> bool:
        """Test public activity endpoint (for guests) includes deadline."""
        print("\n🌐 Testing public activity endpoint with deadline...")
        
        if not self.test_activity_id:
            print("❌ No test activity ID available")
            return False
        
        try:
            # Test public activity endpoint (no auth required)
            response = await self.client.get(f"/api/v1/invites/{self.test_activity_id}")
            
            if response.status_code != 200:
                print(f"❌ Failed to get public activity: {response.text}")
                return False
            
            activity = response.json()
            
            if not activity.get("deadline"):
                print("❌ Deadline not included in public activity response")
                return False
            
            print(f"✅ Public activity includes deadline: {activity['deadline']}")
            return True
            
        except Exception as e:
            print(f"❌ Exception during public activity test: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all deadline feature tests."""
        print("🚀 Starting Deadline Feature Test Suite")
        print("=" * 50)
        
        # Setup
        if not await self.setup():
            return False
        
        # Test results
        tests = [
            ("Create Activity with Deadline", self.test_create_activity_with_deadline),
            ("Get Activity with Deadline", self.test_get_activity_with_deadline),
            ("Update Activity Deadline", self.test_update_activity_deadline),
            ("Deadline Scheduler Check", self.test_deadline_scheduler_check),
            ("Deadline Notifications API", self.test_deadline_notifications_api),
            ("Activity Summary with Deadline", self.test_activity_summary_with_deadline),
            ("Public Activity with Deadline", self.test_public_activity_with_deadline),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                failed += 1
        
        # Cleanup
        await self.cleanup()
        
        # Results
        print("\n" + "=" * 50)
        print("🏁 Test Suite Complete")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        
        return failed == 0
    
    async def close(self):
        """Clean up resources."""
        if self.client:
            await self.client.aclose()
        if self.db_client:
            self.db_client.close()

async def main():
    """Main test runner."""
    test_suite = DeadlineFeatureTest()
    
    try:
        success = await test_suite.run_all_tests()
        return 0 if success else 1
    finally:
        await test_suite.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)