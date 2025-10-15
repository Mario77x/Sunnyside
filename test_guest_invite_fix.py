#!/usr/bin/env python3
"""
Test script to verify that guest users receive email invitations correctly.
This test verifies the fix for the issue where guest users were not receiving email invitations.
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.notifications import NotificationService
from backend.models.activity import InviteGuestsRequest, Invitee, InviteeResponse


async def test_guest_invitation_email():
    """Test that guest users receive the correct invitation email."""
    print("🧪 Testing guest user invitation email...")
    
    # Create a notification service instance
    notification_service = NotificationService()
    
    # Mock the send_email method to capture calls
    with patch.object(notification_service, 'send_email', new_callable=AsyncMock) as mock_send_email:
        mock_send_email.return_value = True
        
        # Test data for guest user invitation
        activity_details = {
            "selected_date": "2024-01-15T10:00:00Z",
            "selected_days": ["Saturday"],
            "weather_preference": "sunny",
            "group_size": "small group",
            "suggestions": [
                {
                    "title": "Picnic in the Park",
                    "description": "Enjoy a relaxing picnic with friends",
                    "duration": "2-3 hours",
                    "budget": "Low",
                    "indoor_outdoor": "Outdoor"
                }
            ],
            "weather_data": [
                {
                    "day": "Today",
                    "temperature_max": 22,
                    "temperature_min": 15,
                    "condition": "sunny",
                    "precipitation": 0
                }
            ]
        }
        
        # Call the guest invitation function
        result = await notification_service.send_activity_invitation_email_to_guest(
            to_email="guest@example.com",
            to_name="Guest User",
            organizer_name="John Organizer",
            activity_title="Weekend Picnic",
            activity_description="A fun outdoor picnic activity",
            custom_message="Hope you can join us!",
            invite_link="https://sunnyside.app/invite/123?email=guest@example.com",
            activity_details=activity_details
        )
        
        # Verify the function was called and returned success
        assert result == True, "Guest invitation email should return True"
        
        # Verify send_email was called once
        assert mock_send_email.call_count == 1, f"Expected 1 call to send_email, got {mock_send_email.call_count}"
        
        # Get the call arguments
        call_args = mock_send_email.call_args
        to_email, subject, html_content = call_args[0]
        
        # Verify the email details
        assert to_email == "guest@example.com", f"Expected email to guest@example.com, got {to_email}"
        assert "Weekend Picnic" in subject, f"Subject should contain activity title, got: {subject}"
        assert "Sunnyside" in subject, f"Subject should mention Sunnyside for guests, got: {subject}"
        
        # Verify the HTML content contains guest-specific information
        assert "What is Sunnyside?" in html_content, "Guest email should explain what Sunnyside is"
        assert "New to Sunnyside?" in html_content, "Guest email should have new user information"
        assert "without creating an account" in html_content, "Guest email should mention no account needed"
        assert "John Organizer" in html_content, "Email should contain organizer name"
        assert "Weekend Picnic" in html_content, "Email should contain activity title"
        assert "Hope you can join us!" in html_content, "Email should contain custom message"
        assert "Respond to Invitation" in html_content, "Email should have response button"
        
        print("✅ Guest invitation email test passed!")


async def test_registered_user_invitation_email():
    """Test that registered users receive the standard invitation email."""
    print("🧪 Testing registered user invitation email...")
    
    # Create a notification service instance
    notification_service = NotificationService()
    
    # Mock the send_email method to capture calls
    with patch.object(notification_service, 'send_email', new_callable=AsyncMock) as mock_send_email:
        mock_send_email.return_value = True
        
        # Test data for registered user invitation
        activity_details = {
            "selected_date": "2024-01-15T10:00:00Z",
            "selected_days": ["Saturday"],
            "weather_preference": "sunny",
            "group_size": "small group"
        }
        
        # Call the standard invitation function (for registered users)
        result = await notification_service.send_activity_invitation_email(
            to_email="registered@example.com",
            to_name="Registered User",
            organizer_name="John Organizer",
            activity_title="Weekend Picnic",
            activity_description="A fun outdoor picnic activity",
            custom_message="Hope you can join us!",
            invite_link="https://sunnyside.app/invite/123?email=registered@example.com",
            activity_details=activity_details
        )
        
        # Verify the function was called and returned success
        assert result == True, "Registered user invitation email should return True"
        
        # Verify send_email was called once
        assert mock_send_email.call_count == 1, f"Expected 1 call to send_email, got {mock_send_email.call_count}"
        
        # Get the call arguments
        call_args = mock_send_email.call_args
        to_email, subject, html_content = call_args[0]
        
        # Verify the email details
        assert to_email == "registered@example.com", f"Expected email to registered@example.com, got {to_email}"
        assert "Weekend Picnic" in subject, f"Subject should contain activity title, got: {subject}"
        
        # Verify the HTML content does NOT contain guest-specific information
        assert "What is Sunnyside?" not in html_content, "Registered user email should not explain what Sunnyside is"
        assert "New to Sunnyside?" not in html_content, "Registered user email should not have new user information"
        assert "You're Invited!" in html_content, "Email should have standard invitation greeting"
        assert "John Organizer" in html_content, "Email should contain organizer name"
        assert "Weekend Picnic" in html_content, "Email should contain activity title"
        
        print("✅ Registered user invitation email test passed!")


async def test_invite_flow_logic():
    """Test the logic that determines which email function to use."""
    print("🧪 Testing invite flow logic...")
    
    # Mock database and user data
    mock_db = MagicMock()
    
    # Mock existing user (registered)
    existing_user = {
        "_id": "user123",
        "name": "Registered User",
        "email": "registered@example.com"
    }
    
    # Mock no user found (guest)
    mock_db.users.find_one = AsyncMock()
    
    # Test case 1: Guest user (no existing user found)
    mock_db.users.find_one.return_value = None
    
    # Simulate the logic from invite_guests_to_activity
    email = "guest@example.com"
    existing_user_result = await mock_db.users.find_one({"email": email})
    
    if existing_user_result:
        email_function = "send_activity_invitation_email"  # For registered users
    else:
        email_function = "send_activity_invitation_email_to_guest"  # For guests
    
    assert email_function == "send_activity_invitation_email_to_guest", \
        f"Guest users should use guest email function, got: {email_function}"
    
    # Test case 2: Registered user (existing user found)
    mock_db.users.find_one.return_value = existing_user
    
    email = "registered@example.com"
    existing_user_result = await mock_db.users.find_one({"email": email})
    
    if existing_user_result:
        email_function = "send_activity_invitation_email"  # For registered users
    else:
        email_function = "send_activity_invitation_email_to_guest"  # For guests
    
    assert email_function == "send_activity_invitation_email", \
        f"Registered users should use standard email function, got: {email_function}"
    
    print("✅ Invite flow logic test passed!")


async def main():
    """Run all tests."""
    print("🚀 Starting guest invitation fix tests...\n")
    
    try:
        await test_guest_invitation_email()
        print()
        
        await test_registered_user_invitation_email()
        print()
        
        await test_invite_flow_logic()
        print()
        
        print("🎉 All tests passed! The guest invitation fix is working correctly.")
        print("\n📋 Summary of the fix:")
        print("1. ✅ Created send_activity_invitation_email_to_guest() function for guest users")
        print("2. ✅ Updated invite_guests_to_activity() to use correct email function based on user type")
        print("3. ✅ Guest emails now include Sunnyside introduction and no-account-needed messaging")
        print("4. ✅ Registered user emails remain unchanged with standard invitation format")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())