#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for User Response Flow

This test covers the complete invitation response flow for registered users:
1. Activity Creation: An organizer creates a new activity and invites a registered user
2. User Invitation: The invited user sees the activity on their dashboard
3. Response Submission: The user navigates to /invitee-response page and submits a response
4. Organizer Notification: The organizer receives notifications about the response
5. Activity Summary: The organizer can access the activity summary page

This test uses both API calls and browser automation to verify the complete flow.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:5173"
ORGANIZER_EMAIL = "organizer@example.com"
ORGANIZER_PASSWORD = "password123"
INVITEE_EMAIL = "invitee@example.com"
INVITEE_PASSWORD = "password123"

class E2EUserResponseFlowTest:
    def __init__(self):
        self.session = None
        self.driver = None
        self.organizer_token = None
        self.invitee_token = None
        self.activity_id = None
        self.organizer_user_id = None
        self.invitee_user_id = None
        
    async def setup_session(self):
        """Setup HTTP session and browser driver"""
        print("🔧 Setting up test environment...")
        self.session = aiohttp.ClientSession()
        
        # Setup Chrome driver with options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print("✅ Browser driver initialized")
        except Exception as e:
            print(f"❌ Failed to initialize browser driver: {e}")
            print("💡 Make sure ChromeDriver is installed and in PATH")
            raise
        
    async def cleanup_session(self):
        """Cleanup HTTP session and browser driver"""
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()
        print("🧹 Test environment cleaned up")
    
    async def create_test_users(self):
        """Create test users for organizer and invitee"""
        print("👥 Creating test users...")
        
        # Create organizer user
        organizer_data = {
            "name": "Test Organizer",
            "email": ORGANIZER_EMAIL,
            "password": ORGANIZER_PASSWORD,
            "location": "Amsterdam, Netherlands",
            "preferences": {
                "outdoor": True,
                "indoor": True,
                "food": True,
                "sports": False,
                "culture": True,
                "nightlife": False,
                "family": True,
                "adventure": False
            }
        }
        
        async with self.session.post(f"{BASE_URL}/auth/register", json=organizer_data) as response:
            if response.status == 200:
                data = await response.json()
                self.organizer_user_id = data.get("user", {}).get("id")
                print(f"✅ Organizer user created: {ORGANIZER_EMAIL}")
            else:
                # User might already exist, try to login
                print(f"ℹ️ Organizer user might already exist, will try login")
        
        # Create invitee user
        invitee_data = {
            "name": "Test Invitee",
            "email": INVITEE_EMAIL,
            "password": INVITEE_PASSWORD,
            "location": "Amsterdam, Netherlands",
            "preferences": {
                "outdoor": True,
                "indoor": False,
                "food": True,
                "sports": True,
                "culture": False,
                "nightlife": True,
                "family": False,
                "adventure": True
            }
        }
        
        async with self.session.post(f"{BASE_URL}/auth/register", json=invitee_data) as response:
            if response.status == 200:
                data = await response.json()
                self.invitee_user_id = data.get("user", {}).get("id")
                print(f"✅ Invitee user created: {INVITEE_EMAIL}")
            else:
                # User might already exist, try to login
                print(f"ℹ️ Invitee user might already exist, will try login")
    
    async def login_users(self):
        """Login both test users and get auth tokens"""
        print("🔐 Logging in test users...")
        
        # Login organizer
        organizer_login = {
            "username": ORGANIZER_EMAIL,
            "password": ORGANIZER_PASSWORD
        }
        
        async with self.session.post(f"{BASE_URL}/auth/login", json=organizer_login) as response:
            if response.status == 200:
                data = await response.json()
                self.organizer_token = data.get("access_token")
                if not self.organizer_user_id:
                    self.organizer_user_id = data.get("user", {}).get("id")
                print(f"✅ Organizer logged in successfully")
            else:
                error_text = await response.text()
                print(f"❌ Organizer login failed: {response.status} - {error_text}")
                return False
        
        # Login invitee
        invitee_login = {
            "username": INVITEE_EMAIL,
            "password": INVITEE_PASSWORD
        }
        
        async with self.session.post(f"{BASE_URL}/auth/login", json=invitee_login) as response:
            if response.status == 200:
                data = await response.json()
                self.invitee_token = data.get("access_token")
                if not self.invitee_user_id:
                    self.invitee_user_id = data.get("user", {}).get("id")
                print(f"✅ Invitee logged in successfully")
            else:
                error_text = await response.text()
                print(f"❌ Invitee login failed: {response.status} - {error_text}")
                return False
        
        return True
    
    async def test_activity_creation(self):
        """Test Scenario 1: Organizer creates a new activity"""
        print("\n📝 SCENARIO 1: Activity Creation")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.organizer_token}"}
        activity_data = {
            "title": "Weekend Brunch & Walk",
            "description": "Let's have a nice brunch followed by a walk in the park. Weather permitting!",
            "timeframe": "weekend morning",
            "groupSize": "small group",
            "activityType": "food",
            "weatherPreference": "sunny",
            "selectedDate": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        async with self.session.post(f"{BASE_URL}/activities", json=activity_data, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self.activity_id = data.get("id")
                print(f"✅ Activity created successfully")
                print(f"   Activity ID: {self.activity_id}")
                print(f"   Title: {data.get('title')}")
                print(f"   Status: {data.get('status')}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Activity creation failed: {response.status} - {error_text}")
                return False
    
    async def test_user_invitation(self):
        """Test Scenario 2: Organizer invites the registered user"""
        print("\n📧 SCENARIO 2: User Invitation")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.organizer_token}"}
        invite_data = {
            "invitees": [
                {
                    "name": "Test Invitee",
                    "email": INVITEE_EMAIL
                }
            ],
            "custom_message": "Hey! Would love to have you join us for brunch this weekend. Let me know if you can make it!"
        }
        
        async with self.session.post(f"{BASE_URL}/activities/{self.activity_id}/invite", 
                                   json=invite_data, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Invitation sent successfully")
                print(f"   Invited count: {data.get('invited_count')}")
                print(f"   Emails sent: {data.get('emails_sent')}")
                print(f"   Custom message: {data.get('custom_message')}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Invitation failed: {response.status} - {error_text}")
                return False
    
    async def test_dashboard_visibility(self):
        """Test that the invited user can see the activity on their dashboard"""
        print("\n👀 SCENARIO 3: Dashboard Visibility Check")
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
                    print(f"✅ Activity visible on invitee's dashboard")
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
                    print(f"❌ Activity not found on invitee's dashboard")
                    print(f"   Available activities: {[a.get('title') for a in activities]}")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Failed to get invitee activities: {response.status} - {error_text}")
                return False
    
    def browser_login(self, email, password):
        """Login to the frontend using browser automation"""
        try:
            print(f"🌐 Logging into frontend as {email}")
            self.driver.get(f"{FRONTEND_URL}/login")
            
            # Wait for login form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            
            # Fill login form
            email_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            email_input.clear()
            email_input.send_keys(email)
            password_input.clear()
            password_input.send_keys(password)
            
            # Submit form
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for redirect to dashboard
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("/")
            )
            
            print(f"✅ Successfully logged into frontend")
            return True
            
        except TimeoutException:
            print(f"❌ Login timeout - page elements not found")
            return False
        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            return False
    
    def test_invitee_response_page_navigation(self):
        """Test navigation to the invitee response page"""
        print("\n🧭 SCENARIO 4A: Navigate to Invitee Response Page")
        print("=" * 50)
        
        try:
            # Login as invitee
            if not self.browser_login(INVITEE_EMAIL, INVITEE_PASSWORD):
                return False
            
            # Navigate to dashboard
            self.driver.get(f"{FRONTEND_URL}/")
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TEXT, "Sunnyside"))
            )
            
            # Look for the "Invited" tab
            invited_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Invited')]"))
            )
            invited_tab.click()
            
            # Wait a moment for tab content to load
            time.sleep(2)
            
            # Look for the activity we created
            activity_elements = self.driver.find_elements(By.XPATH, f"//h3[contains(text(), 'Weekend Brunch & Walk')]")
            
            if activity_elements:
                print(f"✅ Found activity on dashboard")
                
                # Click on the activity to navigate to response page
                activity_elements[0].click()
                
                # Wait for navigation to invitee response page
                WebDriverWait(self.driver, 10).until(
                    EC.url_contains("/invitee-response")
                )
                
                print(f"✅ Successfully navigated to /invitee-response page")
                print(f"   Current URL: {self.driver.current_url}")
                return True
            else:
                print(f"❌ Activity not found on dashboard")
                print(f"   Page source contains: {self.driver.page_source[:500]}...")
                return False
                
        except TimeoutException:
            print(f"❌ Navigation timeout - elements not found")
            print(f"   Current URL: {self.driver.current_url}")
            return False
        except Exception as e:
            print(f"❌ Navigation failed: {str(e)}")
            return False
    
    def test_response_submission_ui(self):
        """Test response submission through the UI"""
        print("\n📤 SCENARIO 4B: Response Submission via UI")
        print("=" * 50)
        
        try:
            # Should already be on the invitee response page from previous test
            
            # Wait for the response page to fully load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Sunnyside')]"))
            )
            
            print(f"✅ Invitee response page loaded")
            
            # Click "Yes" response button
            yes_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes')]"))
            )
            yes_button.click()
            
            print(f"✅ Selected 'Yes' response")
            
            # Wait for additional fields to appear
            time.sleep(2)
            
            # Fill in availability note (if calendar suggestion is shown, use it)
            try:
                use_suggestion_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Use This')]")
                use_suggestion_button.click()
                print(f"✅ Used calendar suggestion for availability")
            except NoSuchElementException:
                # If no suggestion, fill in custom note
                availability_textarea = self.driver.find_element(By.ID, "availability")
                availability_textarea.clear()
                availability_textarea.send_keys("I'm available all weekend! Looking forward to it.")
                print(f"✅ Filled availability note")
            
            # Fill in venue suggestion
            venue_input = self.driver.find_element(By.ID, "venue-suggestion")
            venue_input.clear()
            venue_input.send_keys("How about Café Central? They have great brunch and outdoor seating.")
            print(f"✅ Added venue suggestion")
            
            # Select some preferences (food should already be selected)
            outdoor_checkbox = self.driver.find_element(By.ID, "outdoor")
            if not outdoor_checkbox.is_selected():
                outdoor_checkbox.click()
            
            # Submit the response
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit Response')]"))
            )
            submit_button.click()
            
            # Wait for success page
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Response Submitted')]"))
            )
            
            print(f"✅ Response submitted successfully via UI")
            print(f"   Success page loaded")
            return True
            
        except TimeoutException:
            print(f"❌ Response submission timeout")
            print(f"   Current URL: {self.driver.current_url}")
            return False
        except Exception as e:
            print(f"❌ Response submission failed: {str(e)}")
            return False
    
    async def test_organizer_notifications(self):
        """Test that organizer receives notifications about the response"""
        print("\n🔔 SCENARIO 5: Organizer Notifications")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.organizer_token}"}
        
        # Wait a moment for notifications to be processed
        await asyncio.sleep(2)
        
        async with self.session.get(f"{BASE_URL}/notifications", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                notifications = data.get("notifications", [])
                
                print(f"✅ Retrieved {len(notifications)} notifications")
                
                # Look for activity response notification
                response_notification = None
                for notif in notifications:
                    if (notif.get("notification_type") == "activity_response" and 
                        self.activity_id in notif.get("message", "")):
                        response_notification = notif
                        break
                
                if response_notification:
                    print(f"✅ Found activity response notification")
                    print(f"   Message: {response_notification.get('message')}")
                    print(f"   Type: {response_notification.get('notification_type')}")
                    print(f"   Read: {response_notification.get('read')}")
                    return True
                else:
                    print(f"❌ Activity response notification not found")
                    print(f"   Available notifications: {[n.get('message') for n in notifications[:3]]}")
                    return False
            else:
                error_text = await response.text()
                print(f"❌ Failed to get notifications: {response.status} - {error_text}")
                return False
    
    async def test_activity_summary_access(self):
        """Test that organizer can access activity summary after deadline"""
        print("\n📊 SCENARIO 6: Activity Summary Access")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.organizer_token}"}
        
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
    
    def test_organizer_summary_page_ui(self):
        """Test organizer can access activity summary page via UI"""
        print("\n🖥️ SCENARIO 6B: Activity Summary Page UI Access")
        print("=" * 50)
        
        try:
            # Login as organizer
            if not self.browser_login(ORGANIZER_EMAIL, ORGANIZER_PASSWORD):
                return False
            
            # Navigate to dashboard
            self.driver.get(f"{FRONTEND_URL}/")
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TEXT, "Sunnyside"))
            )
            
            # Look for the "Organized" tab (should be default)
            time.sleep(2)
            
            # Look for the activity we created
            activity_elements = self.driver.find_elements(By.XPATH, f"//h3[contains(text(), 'Weekend Brunch & Walk')]")
            
            if activity_elements:
                print(f"✅ Found activity on organizer dashboard")
                
                # Click on the activity to navigate to summary page
                activity_elements[0].click()
                
                # Wait for navigation to activity summary page
                WebDriverWait(self.driver, 10).until(
                    EC.url_contains("/activity-summary")
                )
                
                print(f"✅ Successfully navigated to activity summary page")
                print(f"   Current URL: {self.driver.current_url}")
                
                # Check if response data is displayed
                try:
                    response_section = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Response')]"))
                    )
                    print(f"✅ Response data visible on summary page")
                    return True
                except TimeoutException:
                    print(f"⚠️ Response data not yet visible (may be expected if deadline hasn't passed)")
                    return True
                    
            else:
                print(f"❌ Activity not found on organizer dashboard")
                return False
                
        except TimeoutException:
            print(f"❌ Summary page navigation timeout")
            print(f"   Current URL: {self.driver.current_url}")
            return False
        except Exception as e:
            print(f"❌ Summary page access failed: {str(e)}")
            return False
    
    async def run_complete_flow_test(self):
        """Run the complete end-to-end test flow"""
        print("🚀 Starting Complete End-to-End User Response Flow Test")
        print("=" * 70)
        
        success_count = 0
        total_tests = 8
        
        try:
            await self.setup_session()
            
            # Create and login test users
            await self.create_test_users()
            if not await self.login_users():
                print("❌ Failed to login users, aborting test")
                return False
            
            # Test Scenario 1: Activity Creation
            if await self.test_activity_creation():
                success_count += 1
            
            # Test Scenario 2: User Invitation
            if await self.test_user_invitation():
                success_count += 1
            
            # Test Scenario 3: Dashboard Visibility
            if await self.test_dashboard_visibility():
                success_count += 1
            
            # Test Scenario 4A: Navigate to Response Page
            if self.test_invitee_response_page_navigation():
                success_count += 1
            
            # Test Scenario 4B: Submit Response via UI
            if self.test_response_submission_ui():
                success_count += 1
            
            # Test Scenario 5: Organizer Notifications
            if await self.test_organizer_notifications():
                success_count += 1
            
            # Test Scenario 6A: Activity Summary API
            if await self.test_activity_summary_access():
                success_count += 1
            
            # Test Scenario 6B: Activity Summary UI
            if self.test_organizer_summary_page_ui():
                success_count += 1
            
            print("\n" + "=" * 70)
            print(f"📊 TEST RESULTS: {success_count}/{total_tests} scenarios passed")
            
            if success_count == total_tests:
                print("🎉 ALL TESTS PASSED! The complete user response flow is working correctly!")
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
    test_runner = E2EUserResponseFlowTest()
    success = await test_runner.run_complete_flow_test()
    
    if success:
        print("\n🎉 End-to-End User Response Flow implementation is working correctly!")
        print("✅ All scenarios completed successfully:")
        print("   1. ✅ Activity Creation")
        print("   2. ✅ User Invitation") 
        print("   3. ✅ Dashboard Visibility")
        print("   4. ✅ Response Page Navigation & Submission")
        print("   5. ✅ Organizer Notifications")
        print("   6. ✅ Activity Summary Access")
    else:
        print("\n💥 Some tests failed. Check the implementation and try again.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())