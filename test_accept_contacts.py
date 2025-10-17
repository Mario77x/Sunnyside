#!/usr/bin/env python3
"""
Test script to accept contact requests so we can test the contact selection UI.
"""

import asyncio
import aiohttp
import json

# Test environment configuration
API_BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@testy.com"
TEST_PASSWORD = "W^XXT$%L7hddx*GJSJEp"

# Test contact emails
TEST_CONTACT_EMAILS = [
    "alice@example.com",
    "bob@example.com", 
    "charlie@example.com"
]

async def login_and_get_token(email, password):
    """Login and get authentication token."""
    async with aiohttp.ClientSession() as session:
        login_data = {
            "username": email,
            "password": password
        }
        
        async with session.post(f"{API_BASE_URL}/api/v1/auth/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("access_token")
            else:
                print(f"Login failed for {email}: {response.status}")
                return None

async def get_contact_requests(session, token):
    """Get pending contact requests."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with session.get(f"{API_BASE_URL}/api/v1/contacts/requests", headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            return data.get("contacts", [])
        else:
            print(f"Failed to get contact requests: {response.status}")
            return []

async def accept_contact_request(session, token, contact_id):
    """Accept a contact request."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response_data = {"action": "accept"}
    
    async with session.post(f"{API_BASE_URL}/api/v1/contacts/{contact_id}/respond", 
                           json=response_data, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            return True
        else:
            error_text = await response.text()
            print(f"Failed to accept contact request {contact_id}: {response.status} - {error_text}")
            return False

async def main():
    """Main function to accept contact requests."""
    print("🚀 Starting contact acceptance process...")
    
    # Accept contact requests for each test contact
    for contact_email in TEST_CONTACT_EMAILS:
        print(f"\n🔐 Logging in as {contact_email}...")
        token = await login_and_get_token(contact_email, "testpassword123")
        
        if not token:
            print(f"❌ Failed to get authentication token for {contact_email}")
            continue
        
        print(f"✅ Successfully authenticated as {contact_email}")
        
        # Get pending contact requests
        async with aiohttp.ClientSession() as session:
            contact_requests = await get_contact_requests(session, token)
            
            if not contact_requests:
                print(f"ℹ️  No pending contact requests for {contact_email}")
                continue
            
            print(f"📋 Found {len(contact_requests)} contact request(s) for {contact_email}")
            
            # Accept all contact requests from the test user
            for request in contact_requests:
                if request.get("contact_email") == TEST_EMAIL:
                    contact_id = request.get("id")
                    if await accept_contact_request(session, token, contact_id):
                        print(f"✅ Accepted contact request from {TEST_EMAIL}")
                    else:
                        print(f"❌ Failed to accept contact request from {TEST_EMAIL}")
    
    print(f"\n🎉 Contact acceptance process complete!")
    print("Now the test user should have accepted contacts that will appear in the contact selection UI.")

if __name__ == "__main__":
    asyncio.run(main())