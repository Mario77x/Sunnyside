#!/usr/bin/env python3

import pytest
import pytest_asyncio
import httpx
from datetime import datetime, timedelta
import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Test configuration
TEST_PORT = 8000
TEST_EMAIL = "test@testy.com"
TEST_PASSWORD = "W^XXT$%L7hddx*GJSJEp"
TEST_USER_NAME = "Testy user"
BASE_URL = f"http://localhost:{TEST_PORT}"

@pytest_asyncio.fixture(scope="module")
async def auth_token():
    """Fixture to get an authentication token."""
    async with httpx.AsyncClient() as client:
        login_data = {"username": TEST_EMAIL, "password": TEST_PASSWORD}
        try:
            response = await client.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
            response.raise_for_status()
            return response.json()["access_token"]
        except httpx.HTTPStatusError as e:
            pytest.fail(f"Login failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            pytest.fail(f"An error occurred during login: {e}")

@pytest_asyncio.fixture(scope="module")
async def test_activity_id(auth_token):
    """Fixture to create a test activity and return its ID."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    activity_data = {
        "title": "Weekend Brunch Finalization Test",
        "description": "Testing the finalization flow with confirmed attendees",
        "timeframe": "Weekend morning",
        "groupSize": "small group",
        "activityType": "food",
        "weatherPreference": "either",
        "selectedDate": (datetime.now() + timedelta(days=7)).isoformat(),
        "deadline": (datetime.now() + timedelta(days=3)).isoformat()
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/api/v1/activities", json=activity_data, headers=headers)
            response.raise_for_status()
            activity = response.json()
            activity_id = activity["id"]

            # Add invitees and simulate responses
            await add_test_invitees(activity_id, auth_token)
            await simulate_invitee_responses(activity_id, auth_token)
            
            return activity_id
        except httpx.HTTPStatusError as e:
            pytest.fail(f"Failed to create activity: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            pytest.fail(f"An error occurred during activity creation: {e}")

async def add_test_invitees(activity_id, auth_token):
    """Helper function to add test invitees."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    invite_data = {
        "invitees": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
            {"name": "Carol Davis", "email": "carol@example.com"}
        ],
        "custom_message": "Looking forward to our brunch together!",
        "channel": "email"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/v1/activities/{activity_id}/invite", json=invite_data, headers=headers)
        response.raise_for_status()

async def simulate_invitee_responses(activity_id, auth_token):
    """Helper function to simulate invitee responses."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient() as client:
        # This is a simplified simulation. A more robust test would create and log in as invitees.
        update_data = {
            "status": "responses-collected",
            "invitees": [
                {"name": "Alice Johnson", "email": "alice@example.com", "response": "yes"},
                {"name": "Bob Smith", "email": "bob@example.com", "response": "yes"},
                {"name": "Carol Davis", "email": "carol@example.com", "response": "no"}
            ]
        }
        response = await client.put(f"{BASE_URL}/api/v1/activities/{activity_id}", json=update_data, headers=headers)
        response.raise_for_status()

@pytest.mark.asyncio
@pytest.mark.order(1)
async def test_finalization_recommendations(test_activity_id, auth_token):
    """Test the finalization recommendations endpoint."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/v1/activities/{test_activity_id}/finalization-recommendations", headers=headers)
        assert response.status_code == 200
        result = response.json()
        assert "date_recommendations" in result
        assert "venue_recommendations" in result
        assert "confirmed_attendees" in result

@pytest.mark.asyncio
@pytest.mark.order(2)
async def test_activity_finalization(test_activity_id, auth_token):
    """Test the activity finalization endpoint."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    finalization_data = {
        "finalized_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "finalized_time": "10:30",
        "finalized_venue": {
            "name": "The Garden Café",
            "address": "123 Main Street, Downtown",
            "type": "restaurant",
            "phone": "+31 20 123 4567"
        },
        "final_message": "Looking forward to seeing everyone at The Garden Café!"
    }
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{BASE_URL}/api/v1/activities/{test_activity_id}/finalize", json=finalization_data, headers=headers)
        assert response.status_code == 200
        result = response.json()
        assert result.get("finalized_venue", {}).get("name") == "The Garden Café"

@pytest.mark.asyncio
@pytest.mark.order(3)
async def test_final_invites(test_activity_id, auth_token):
    """Test sending final invites."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    invite_data = {
        "communication_preferences": {
            "alice@example.com": "email",
            "bob@example.com": "email",
            "carol@example.com": "email"
        },
        "custom_message": "Final details confirmed! See you at The Garden Café on Saturday at 10:30 AM."
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/v1/activities/{test_activity_id}/final-invites", json=invite_data, headers=headers)
        assert response.status_code == 200
        result = response.json()
        assert result.get("invites_sent") > 0

@pytest.mark.asyncio
@pytest.mark.order(4)
async def test_calendar_integration(test_activity_id, auth_token):
    """Test calendar integration."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    calendar_data = {
        "calendar_provider": "google",
        "event_details": {
            "reminder_minutes": 30,
            "include_attendees": True
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/v1/activities/{test_activity_id}/add-to-calendar", json=calendar_data, headers=headers)
        assert response.status_code == 200
        result = response.json()
        assert result.get("calendar_integration_status") == "integrated"

@pytest.mark.asyncio
@pytest.mark.order(5)
async def test_calendar_file_download(test_activity_id, auth_token):
    """Test calendar file download."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/activities/{test_activity_id}/calendar-file", headers=headers)
        assert response.status_code == 200
        ics_content = response.text
        assert "BEGIN:VCALENDAR" in ics_content
        assert "END:VCALENDAR" in ics_content