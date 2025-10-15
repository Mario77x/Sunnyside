#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Invitee Summary Flow

This test covers the complete flow for the new read-only summary page functionality:

1. Activity Creation and Invitation: An organizer creates an activity and invites a registered user
2. Initial Response: The invited user submits their response via /invitee-response page
3. Navigation to Summary: After response, user navigates back to dashboard and clicks activity again
4. Summary Page Verification: User is taken to /invitee-activity-summary page (read-only)
5. No Editing: Verify that the user cannot edit their response from the summary page
6. Data Flow Verification: Ensure data flows correctly between frontend and backend

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
from selenium.webdriver.common.action_chains import ActionChains

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:5173"
ORGANIZER_EMAIL = "organizer.summary@example.com"
ORGANIZER_PASSWORD = "password123"
INVITEE_EMAIL = "invitee.summary@example.com"
INVITEE_PASSWORD = "password123"

class InviteeSummaryFlowTest:
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
            "name": "Test Organizer Summary",
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
                print(f"ℹ️ Organizer user might already exist, will try login")
        
        # Create invitee user
        invitee_data = {
            "name": "Test Invitee Summary",
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
    
    async def test_activity_creation_and_invitation(self):
        """Test Scenario 1: Organizer creates activity and invites user"""
        print("\n📝 SCENARIO 1: Activity Creation and Invitation")
        print("=" * 50)
        
        headers = {"Authorization": f"Bearer {self.organizer_token}"}
        
        # Create activity
        activity_data = {
            "title": "Weekend Coffee & Museum Visit",
            "description": "Let's grab coffee and visit the new art exhibition at the museum. Perfect for a relaxed weekend!",
            "timeframe": "weekend afternoon",
            "groupSize": "small group",
            "activityType": "culture",
            "weatherPreference": "either",
            "selectedDate": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        async with self.session.post(f"{BASE_URL}/activities", json=activity_data, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self.activity_id = data.get("id")
                print(f"✅ Activity created successfully")
                print(f"   Activity ID: {self.activity_id}")
                print(f"   Title: {data.get('title')}")
            else:
                error_text = await response.text()
                print(f"❌ Activity creation failed: {response.status} - {error_text}")
                return False
        
        # Send invitation
        invite_data = {
            "invitees": [
                {
                    "name": "Test Invitee Summary",
                    "email": INVITEE_EMAIL
                }
            ],
            "custom_message": "Hey! Would love to have you join us for coffee and culture this weekend. Let me know if you're interested!"
        }
        
        async with self.session.post(f"{BASE_URL}/activities/{self.activity_id}/invite", 
                                   json=invite_data, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Invitation sent successfully")
                print(f"   Invited count: {data.get('invited_count')}")
                print(f"   Emails sent: {data.get('emails_sent')}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ Invitation failed: {response.status} - {error_text}")
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
    
    def test_initial_response_submission(self):
        """Test Scenario 2: User submits initial response via UI"""
        print("\n📤 SCENARIO 2: Initial Response Submission")
        print("=" * 50)
        
        try:
            # Login as invitee
            if not self.browser_login(INVITEE_EMAIL, INVITEE_PASSWORD):
                return False
            
            # Navigate to dashboard
            self.driver.get(f"{FRONTEND_URL}/")
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Sunnyside')]"))
            )
            
            # Click on the "Invited" tab
            invited_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Invited')]"))
            )
            invited_tab.click()
            
            # Wait for tab content to load
            time.sleep(2)
            
            # Look for the activity we created
            activity_elements = self.driver.find_elements(By.XPATH, f"//h3[contains(text(), 'Weekend Coffee & Museum Visit')]")
            
            if activity_elements:
                print(f"✅ Found activity on dashboard")
                
                # Click on the activity to navigate to response page
                activity_elements[0].click()
                
                # Wait for navigation to invitee response page
                WebDriverWait(self.driver, 10).until(
                    EC.url_contains("/invitee-response")
                )
                
                print(f"✅ Successfully navigated to /invitee-response page")
                
                # Wait for the response page to fully load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Sunnyside')]"))
                )
                
                # Click "Yes" response button
                yes_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes')]"))
                )
                yes_button.click()
                
                print(f"✅ Selected 'Yes' response")
                
                # Wait for additional fields to appear
                time.sleep(2)
                
                # Handle availability note (try calendar suggestion first)
                try:
                    use_suggestion_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Use This')]")
                    use_suggestion_button.click()
                    print(f"✅ Used calendar suggestion for availability")
                except NoSuchElementException:
                    # If no suggestion, fill in custom note
                    try:
                        availability_textarea = self.driver.find_element(By.ID, "availability")
                        availability_textarea.clear()
                        availability_textarea.send_keys("I'm available all weekend! Looking forward to the museum visit.")
                        print(f"✅ Filled availability note")
                    except NoSuchElementException:
                        print(f"⚠️ No availability field found")
                
                # Fill in venue suggestion
                try:
                    venue_input = self.driver.find_element(By.ID, "venue-suggestion")
                    venue_input.clear()
                    venue_input.send_keys("How about starting at Café de Reiger and then visiting the Rijksmuseum?")
                    print(f"✅ Added venue suggestion")
                except NoSuchElementException:
                    print(f"⚠️ No venue suggestion field found")
                
                # Select some preferences
                try:
                    culture_checkbox = self.driver.find_element(By.ID, "culture")
                    if not culture_checkbox.is_selected():
                        culture_checkbox.click()
                    print(f"✅ Selected culture preference")
                except NoSuchElementException:
                    print(f"⚠️ Culture checkbox not found")
                
                # Submit the response
                submit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit Response')]"))
                )
                submit_button.click()
                
                # Wait for success page
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Response Submitted')]"))
                )
                
                print(f"✅ Response submitted successfully via UI")
                return True
                
            else:
                print(f"❌ Activity not found on dashboard")
                return False
                
        except TimeoutException:
            print(f"❌ Response submission timeout")
            print(f"   Current URL: {self.driver.current_url}")
            return False
        except Exception as e:
            print(f"❌ Response submission failed: {str(e)}")
            return False
    
    def test_navigation_to_summary_page(self):
        """Test Scenario 3: Navigate back to dashboard and access summary page"""
        print("\n🧭 SCENARIO 3: Navigation to Summary Page")
        print("=" * 50)
        
        try:
            # Click "Back to Dashboard" button from success page
            back_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Back to Dashboard')]"))
            )
            back_button.click()
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Sunnyside')]"))
            )
            
            print(f"✅ Navigated back to dashboard")
            
            # Click on the "Invited" tab again
            invited_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Invited')]"))
            )
            invited_tab.click()
            
            # Wait for tab content to load
            time.sleep(2)
            
            # Click on the same activity again
            activity_elements = self.driver.find_elements(By.XPATH, f"//h3[contains(text(), 'Weekend Coffee & Museum Visit')]")
            
            if activity_elements:
                print(f"✅ Found activity on dashboard again")
                
                # Click on the activity - this time should navigate to summary page
                activity_elements[0].click()
                
                # Wait for navigation to invitee activity summary page
                WebDriverWait(self.driver, 10).until(
                    EC.url_contains("/invitee-activity-summary")
                )
                
                print(f"✅ Successfully navigated to /invitee-activity-summary page")
                print(f"   Current URL: {self.driver.current_url}")
                return True
                
            else:
                print(f"❌ Activity not found on dashboard")
                return False
                
        except TimeoutException:
            print(f"❌ Navigation to summary page timeout")
            print(f"   Current URL: {self.driver.current_url}")
            return False
        except Exception as e:
            print(f"❌ Navigation to summary page failed: {str(e)}")
            return False
    
    def test_summary_page_verification(self):
        """Test Scenario 4: Verify summary page displays correct data in read-only format"""
        print("\n📊 SCENARIO 4: Summary Page Verification")
        print("=" * 50)
        
        try:
            # Wait for summary page to fully load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Activity Summary')]"))
            )
            
            print(f"✅ Summary page loaded successfully")
            
            # Verify response status is displayed
            response_status = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Your Response Submitted')]"))
            )
            print(f"✅ Response status displayed: {response_status.text}")
            
            # Verify activity details are shown
            activity_title = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Weekend Coffee & Museum Visit')]")
            print(f"✅ Activity title displayed: {activity_title.text}")
            
            # Verify user's response details are shown
            response_details_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Your Response Details')]")
            print(f"✅ Response details section found")
            
            # Check for user's response (should show "yes")
            try:
                yes_badge = self.driver.find_element(By.XPATH, "//span[contains(text(), 'yes')]")
                print(f"✅ User's 'yes' response displayed")
            except NoSuchElementException:
                print(f"⚠️ User's response badge not found")
            
            # Check for availability note
            try:
                availability_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Your Availability Note')]")
                print(f"✅ Availability note section found")
            except NoSuchElementException:
                print(f"⚠️ Availability note section not found")
            
            # Check for venue suggestion
            try:
                venue_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Your Venue Suggestion')]")
                print(f"✅ Venue suggestion section found")
            except NoSuchElementException:
                print(f"⚠️ Venue suggestion section not found")
            
            # Check for activity preferences
            try:
                preferences_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Your Activity Preferences')]")
                print(f"✅ Activity preferences section found")
            except NoSuchElementException:
                print(f"⚠️ Activity preferences section not found")
            
            # Verify "What's Next?" section is present
            try:
                next_steps_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'What\\'s Next?')]")
                print(f"✅ Next steps section found")
            except NoSuchElementException:
                print(f"⚠️ Next steps section not found")
            
            return True
            
        except TimeoutException:
            print(f"❌ Summary page verification timeout")
            return False
        except Exception as e:
            print(f"❌ Summary page verification failed: {str(e)}")
            return False
    
    def test_no_editing_capability(self):
        """Test Scenario 5: Verify that user cannot edit their response from summary page"""
        print("\n🔒 SCENARIO 5: No Editing Capability Verification")
        print("=" * 50)
        
        try:
            # Look for any form elements that would allow editing
            form_elements = self.driver.find_elements(By.TAG_NAME, "form")
            input_elements = self.driver.find_elements(By.TAG_NAME, "input")
            textarea_elements = self.driver.find_elements(By.TAG_NAME, "textarea")
            select_elements = self.driver.find_elements(By.TAG_NAME, "select")
            
            # Filter out elements that are not for editing responses (like search, navigation, etc.)
            editable_inputs = []
            for input_elem in input_elements:
                input_type = input_elem.get_attribute("type")
                input_id = input_elem.get_attribute("id")
                input_name = input_elem.get_attribute("name")
                
                # Skip navigation, search, and other non-response related inputs
                if (input_type not in ["hidden", "submit", "button"] and 
                    input_id not in ["search", "navigation"] and
                    "search" not in (input_name or "").lower()):
                    editable_inputs.append(input_elem)
            
            print(f"✅ Found {len(form_elements)} forms, {len(editable_inputs)} editable inputs, {len(textarea_elements)} textareas, {len(select_elements)} selects")
            
            # Look for specific response editing elements that should NOT be present
            response_editing_elements = []
            
            # Check for response buttons (Yes/No/Maybe)
            try:
                yes_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Yes') and not(contains(@class, 'disabled'))]")
                if yes_button.is_enabled():
                    response_editing_elements.append("Yes button")
            except NoSuchElementException:
                pass
            
            try:
                no_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'No') and not(contains(@class, 'disabled'))]")
                if no_button.is_enabled():
                    response_editing_elements.append("No button")
            except NoSuchElementException:
                pass
            
            try:
                maybe_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Maybe') and not(contains(@class, 'disabled'))]")
                if maybe_button.is_enabled():
                    response_editing_elements.append("Maybe button")
            except NoSuchElementException:
                pass
            
            # Check for submit response button
            try:
                submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit Response')]")
                if submit_button.is_enabled():
                    response_editing_elements.append("Submit Response button")
            except NoSuchElementException:
                pass
            
            # Check for availability note editing
            try:
                availability_input = self.driver.find_element(By.ID, "availability")
                if availability_input.is_enabled():
                    response_editing_elements.append("Availability textarea")
            except NoSuchElementException:
                pass
            
            # Check for venue suggestion editing
            try:
                venue_input = self.driver.find_element(By.ID, "venue-suggestion")
                if venue_input.is_enabled():
                    response_editing_elements.append("Venue suggestion input")
            except NoSuchElementException:
                pass
            
            # Check for preference checkboxes
            preference_checkboxes = self.driver.find_elements(By.XPATH, "//input[@type='checkbox' and (@id='outdoor' or @id='indoor' or @id='food' or @id='sports' or @id='culture' or @id='nightlife' or @id='family' or @id='adventure')]")
            enabled_checkboxes = [cb for cb in preference_checkboxes if cb.is_enabled()]
            if enabled_checkboxes:
                response_editing_elements.extend([f"Preference checkbox ({cb.get_attribute('id')})" for cb in enabled_checkboxes])
            
            if response_editing_elements:
                print(f"❌ Found editable response elements (should be read-only):")
                for element in response_editing_elements:
                    print(f"   - {element}")
                return False
            else:
                print(f"✅ No editable response elements found - page is properly read-only")
                
                # Verify that data is displayed but not editable
                displayed_data_elements = []
                
                # Check for displayed response data
                try:
                    response_badge = self.driver.find_element(By.XPATH, "//span[contains(@class, 'badge') or contains(@class, 'Badge')]")
                    displayed_data_elements.append("Response badge")
                except NoSuchElementException:
                    pass
                
                # Check for displayed text content
                try:
                    availability_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'available') or contains(text(), 'weekend')]")
                    displayed_data_elements.append("Availability text")
                except NoSuchElementException:
                    pass
                
                try:
                    venue_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Café') or contains(text(), 'museum')]")
                    displayed_data_elements.append("Venue suggestion text")
                except NoSuchElementException:
                    pass
                
                print(f"✅ Found {len(displayed_data_elements)} displayed data elements:")
                for element in displayed_data_elements:
                    print(f"   - {element}")
                
                return True
            
        except Exception as e:
            print(f"❌ No editing capability verification failed: {str(e)}")
            return False
    
    async def test_data_flow_verification(self):
        """Test Scenario 6: Verify data flows correctly between frontend and backend"""
        print("\n🔄 SCENARIO 6: Data Flow Verification")
        print("=" * 50)
        
        try:
            # Get activity data from backend API to verify response was saved
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
                        if "available" in availability_note.lower() or "weekend" in availability_note.lower():
                            print(f"✅ Availability note contains expected content")
                        else:
                            print(f"⚠️ Availability note might not contain expected content: {availability_note}")
                        
                        # Verify venue suggestion contains expected content
                        venue_suggestion = user_response.get("venue_suggestion", "")
                        if "café" in venue_suggestion.lower() or "museum" in venue_suggestion.lower():
                            print(f"✅ Venue suggestion contains expected content")
                        else:
                            print(f"⚠️ Venue suggestion might not contain expected content: {venue_suggestion}")
                        
                        # Verify preferences were saved
                        preferences = user_response.get("preferences", {})
                        if preferences.get("culture") or preferences.get("food"):
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
                    
        except Exception as e:
            print(f"❌ Data flow verification failed: {str(e)}")
            return False
    
    async def run_complete_flow_test(self):
        """Run the complete end-to-end test flow"""
        print("🚀 Starting Complete Invitee Summary Flow Test")
        print("=" * 70)
        
        success_count = 0
        total_tests = 6
        
        try:
            await self.setup_session()
            
            # Create and login test users
            await self.create_test_users()
            if not await self.login_users():
                print("❌ Failed to login users, aborting test")
                return False
            
            # Test Scenario 1: Activity Creation and Invitation
            if await self.test_activity_creation_and_invitation():
                success_count += 1
            
            # Test Scenario 2: Initial Response Submission
            if self.test_initial_response_submission():
                success_count += 1
            
            # Test Scenario 3: Navigation to Summary Page
            if self.test_navigation_to_summary_page():
                success_count += 1
            
            # Test Scenario 4: Summary Page Verification
            if self.test_summary_page_verification():
                success_count += 1
            
            # Test Scenario 5: No Editing Capability
            if self.test_no_editing_capability():
                success_count += 1
            
            # Test Scenario 6: Data Flow Verification
            if await self.test_data_flow_verification():
                success_count += 1
            
            print("\n" + "=" * 70)
            print(f"📊 TEST RESULTS: {success_count}/{total_tests} scenarios passed")
            
            if success_count == total_tests:
                print("🎉 ALL TESTS PASSED! The invitee summary flow is working correctly!")
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
    test_runner = InviteeSummaryFlowTest()
    success = await test_runner.run_complete_flow_test()
    
    if success:
        print("\n🎉 Invitee Summary Flow implementation is working correctly!")
        print("✅ All scenarios completed successfully:")
        print("   1. ✅ Activity Creation and Invitation")
        print("   2. ✅ Initial Response Submission") 
        print("   3. ✅ Navigation to Summary Page")
        print("   4. ✅ Summary Page Verification")
        print("   5. ✅ No Editing Capability")
        print("   6. ✅ Data Flow Verification")
        print("\n🔄 Complete Flow Verified:")
        print("   • Organizer creates activity and invites user ✅")
        print("   • User submits response via /invitee-response ✅")
        print("   • User navigates back to dashboard ✅")
        print("   • User clicks activity again → /invitee-activity-summary ✅")
        print("   • Summary page shows read-only data ✅")
        print("   • No editing capabilities available ✅")
        print("   • Data flows correctly between frontend/backend ✅")
    else:
        print("\n💥 Some tests failed. Check the implementation and try again.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())