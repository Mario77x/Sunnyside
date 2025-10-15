#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.utils.environment import get_invite_link

def test_invite_link_generation():
    """Test that invite links are generated correctly for the guest response page."""
    
    print("Testing invite link generation...")
    
    # Test case 1: Activity ID only
    activity_id = "507f1f77bcf86cd799439011"
    link_without_email = get_invite_link(activity_id)
    expected_without_email = "http://localhost:5137/guest?activity=507f1f77bcf86cd799439011"
    
    print(f"Link without email: {link_without_email}")
    print(f"Expected: {expected_without_email}")
    assert link_without_email == expected_without_email, f"Expected {expected_without_email}, got {link_without_email}"
    print("✅ Link without email - PASSED")
    
    # Test case 2: Activity ID with guest email
    guest_email = "guest@example.com"
    link_with_email = get_invite_link(activity_id, guest_email)
    expected_with_email = "http://localhost:5137/guest?activity=507f1f77bcf86cd799439011&email=guest@example.com"
    
    print(f"Link with email: {link_with_email}")
    print(f"Expected: {expected_with_email}")
    assert link_with_email == expected_with_email, f"Expected {expected_with_email}, got {link_with_email}"
    print("✅ Link with email - PASSED")
    
    print("\n🎉 All invite link generation tests passed!")
    print("\nThe fix ensures that:")
    print("1. Links point to /guest route (matches frontend routing)")
    print("2. Activity ID is passed as ?activity= parameter (matches GuestResponse.tsx)")
    print("3. Guest email is passed as &email= parameter (matches GuestResponse.tsx)")

if __name__ == "__main__":
    test_invite_link_generation()