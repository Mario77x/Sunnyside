#!/usr/bin/env python3
"""
Test script to verify the invited activities fix works correctly.
This script will:
1. Login as the test user
2. Create a test invite where the user is invited
3. Fetch activities to verify the invited activity appears
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@testy.com"
TEST_PASSWORD = "W^XXT$%L7hddx*GJSJEp"

def login():
    """Login and get access token"""
    print("🔐 Logging in...")
    response = requests.post(f"{API_BASE_URL}/api/v1/auth/login", json={
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def create_test_invite(token):
    """Create a test invite where the current user is invited"""
    print("📝 Creating test invite...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{API_BASE_URL}/api/v1/activities/create-test-invite", headers=headers)
    
    if response.status_code == 200:
        activity = response.json()
        print(f"✅ Test invite created: {activity['title']}")
        print(f"   Activity ID: {activity['id']}")
        print(f"   Organizer ID: {activity['organizer_id']}")
        print(f"   Number of invitees: {len(activity['invitees'])}")
        return activity
    else:
        print(f"❌ Failed to create test invite: {response.status_code} - {response.text}")
        return None

def get_activities(token):
    """Get all activities for the current user"""
    print("📋 Fetching user activities...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{API_BASE_URL}/api/v1/activities", headers=headers)
    
    if response.status_code == 200:
        activities = response.json()
        print(f"✅ Found {len(activities)} activities")
        return activities
    else:
        print(f"❌ Failed to fetch activities: {response.status_code} - {response.text}")
        return []

def get_current_user(token):
    """Get current user info"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/api/v1/auth/me", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    return None

def analyze_activities(activities, user_id):
    """Analyze activities to categorize them"""
    organized = []
    invited = []
    
    for activity in activities:
        if activity["organizer_id"] == user_id:
            organized.append(activity)
        else:
            # Check if user is in invitees list
            user_in_invitees = any(
                invitee.get("id") == user_id for invitee in activity.get("invitees", [])
            )
            if user_in_invitees:
                invited.append(activity)
    
    return organized, invited

def main():
    print("🧪 Testing invited activities fix...")
    print("=" * 50)
    
    # Step 1: Login
    token = login()
    if not token:
        return
    
    # Get current user info
    user = get_current_user(token)
    if not user:
        print("❌ Failed to get user info")
        return
    
    print(f"👤 Current user: {user['name']} (ID: {user['id']})")
    print()
    
    # Step 2: Get activities before creating test invite
    print("📊 BEFORE creating test invite:")
    activities_before = get_activities(token)
    organized_before, invited_before = analyze_activities(activities_before, user["id"])
    print(f"   Organized: {len(organized_before)}")
    print(f"   Invited: {len(invited_before)}")
    print()
    
    # Step 3: Create test invite
    test_activity = create_test_invite(token)
    if not test_activity:
        return
    print()
    
    # Step 4: Get activities after creating test invite
    print("📊 AFTER creating test invite:")
    activities_after = get_activities(token)
    organized_after, invited_after = analyze_activities(activities_after, user["id"])
    print(f"   Organized: {len(organized_after)}")
    print(f"   Invited: {len(invited_after)}")
    print()
    
    # Step 5: Verify the fix worked
    print("🔍 VERIFICATION:")
    if len(invited_after) > len(invited_before):
        print("✅ SUCCESS: Invited activities count increased!")
        print("✅ The fix is working correctly - invited activities now appear in the user's dashboard")
        
        # Show details of the invited activity
        new_invited = [a for a in invited_after if a not in invited_before]
        if new_invited:
            activity = new_invited[0]
            print(f"   📝 New invited activity: '{activity['title']}'")
            print(f"   👤 Organized by: Test Organizer")
            print(f"   📅 Status: {activity['status']}")
    else:
        print("❌ FAILED: Invited activities count did not increase")
        print("❌ The fix may not be working correctly")
    
    print("=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    main()