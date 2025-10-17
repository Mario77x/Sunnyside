#!/usr/bin/env python3
"""
Test script to add some contacts for the test user to test contact selection functionality.
"""

import asyncio
import aiohttp
import json

# Test environment configuration
API_BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@testy.com"
TEST_PASSWORD = "W^XXT$%L7hddx*GJSJEp"

# Test contacts to add
TEST_CONTACTS = [
    {
        "contact_email": "alice@example.com",
        "message": "Hi Alice! Let's connect on Sunnyside."
    },
    {
        "contact_email": "bob@example.com", 
        "message": "Hey Bob! Would love to have you as a contact."
    },
    {
        "contact_email": "charlie@example.com",
        "message": "Hi Charlie! Let's stay connected."
    }
]

async def login_and_get_token():
    """Login and get authentication token."""
    async with aiohttp.ClientSession() as session:
        login_data = {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        async with session.post(f"{API_BASE_URL}/api/v1/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("access_token")
            else:
                print(f"Login failed: {response.status}")
                return None

async def add_contact(session, token, contact_data):
    """Add a contact for the test user."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with session.post(f"{API_BASE_URL}/api/v1/contacts/request", 
                           json=contact_data, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            print(f"✅ Contact request sent to {contact_data['contact_email']}: {data.get('message')}")
            return True
        else:
            error_text = await response.text()
            print(f"❌ Failed to add contact {contact_data['contact_email']}: {response.status} - {error_text}")
            return False

async def create_test_users_and_accept_contacts():
    """Create test users and automatically accept contact requests."""
    async with aiohttp.ClientSession() as session:
        # Create test users for the contacts
        for contact in TEST_CONTACTS:
            user_data = {
                "name": contact["contact_email"].split("@")[0].title(),
                "email": contact["contact_email"],
                "password": "testpassword123",
                "location": "Test City"
            }
            
            async with session.post(f"{API_BASE_URL}/api/v1/auth/signup", json=user_data) as response:
                if response.status == 200:
                    print(f"✅ Created test user: {contact['contact_email']}")
                elif response.status == 400:
                    print(f"ℹ️  User {contact['contact_email']} already exists")
                else:
                    print(f"❌ Failed to create user {contact['contact_email']}: {response.status}")

async def main():
    """Main function to add test contacts."""
    print("🚀 Starting contact addition process...")
    
    # First create test users
    print("\n📝 Creating test users...")
    await create_test_users_and_accept_contacts()
    
    # Login and get token
    print(f"\n🔐 Logging in as {TEST_EMAIL}...")
    token = await login_and_get_token()
    
    if not token:
        print("❌ Failed to get authentication token")
        return
    
    print("✅ Successfully authenticated")
    
    # Add contacts
    print(f"\n👥 Adding {len(TEST_CONTACTS)} test contacts...")
    async with aiohttp.ClientSession() as session:
        success_count = 0
        for contact in TEST_CONTACTS:
            if await add_contact(session, token, contact):
                success_count += 1
    
    print(f"\n🎉 Successfully added {success_count}/{len(TEST_CONTACTS)} contacts!")
    print("\nNote: These are pending contact requests. In a real scenario, the contacts would need to accept them.")
    print("For testing purposes, you can now see the contact selection UI in the InviteGuests page.")

if __name__ == "__main__":
    asyncio.run(main())