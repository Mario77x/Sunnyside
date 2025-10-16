#!/usr/bin/env python3
"""
Test script for communication integrations (EmailJS and Twilio)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.services.notifications import NotificationService

async def test_email_integration():
    """Test EmailJS integration"""
    print("🔧 Testing EmailJS Integration...")
    
    notification_service = NotificationService()
    
    # Test basic email sending (will be simulated in local dev)
    success = await notification_service.send_email(
        to_email="test@example.com",
        template_key="activity_invitation",
        template_params={
            "to_name": "Test User",
            "organizer_name": "Test Organizer",
            "activity_title": "Test Activity",
            "activity_description": "This is a test activity",
            "date_info": "Tomorrow",
            "invite_link": "https://example.com/invite"
        },
        subject="Test Activity Invitation"
    )
    
    if success:
        print("✅ EmailJS integration working correctly")
    else:
        print("❌ EmailJS integration failed")
    
    return success

async def test_sms_integration():
    """Test Twilio SMS integration"""
    print("\n📱 Testing Twilio SMS Integration...")
    
    notification_service = NotificationService()
    
    # Test SMS sending (will be simulated in local dev)
    success = await notification_service.send_sms(
        to_phone="+1234567890",
        message="Test SMS from Sunnyside app",
        activity_title="Test Activity"
    )
    
    if success:
        print("✅ Twilio SMS integration working correctly")
    else:
        print("❌ Twilio SMS integration failed")
    
    return success

async def test_whatsapp_integration():
    """Test Twilio WhatsApp integration"""
    print("\n💬 Testing Twilio WhatsApp Integration...")
    
    notification_service = NotificationService()
    
    # Test WhatsApp sending (will be simulated in local dev)
    success = await notification_service.send_whatsapp(
        to_phone="+1234567890",
        message="Test WhatsApp message from Sunnyside app",
        activity_title="Test Activity"
    )
    
    if success:
        print("✅ Twilio WhatsApp integration working correctly")
    else:
        print("❌ Twilio WhatsApp integration failed")
    
    return success

async def test_activity_invitation_methods():
    """Test activity invitation methods for all channels"""
    print("\n🎯 Testing Activity Invitation Methods...")
    
    notification_service = NotificationService()
    
    # Test activity invitation email
    email_success = await notification_service.send_activity_invitation_email(
        to_email="test@example.com",
        to_name="Test User",
        organizer_name="Test Organizer",
        activity_title="Beach Volleyball",
        activity_description="Join us for a fun beach volleyball game!",
        invite_link="https://sunnyside.app/invite/123"
    )
    
    # Test activity invitation SMS
    sms_success = await notification_service.send_activity_invitation_sms(
        to_phone="+1234567890",
        to_name="Test User",
        organizer_name="Test Organizer",
        activity_title="Beach Volleyball",
        activity_description="Join us for a fun beach volleyball game!",
        invite_link="https://sunnyside.app/invite/123"
    )
    
    # Test activity invitation WhatsApp
    whatsapp_success = await notification_service.send_activity_invitation_whatsapp(
        to_phone="+1234567890",
        to_name="Test User",
        organizer_name="Test Organizer",
        activity_title="Beach Volleyball",
        activity_description="Join us for a fun beach volleyball game!",
        invite_link="https://sunnyside.app/invite/123"
    )
    
    print(f"📧 Email invitation: {'✅' if email_success else '❌'}")
    print(f"📱 SMS invitation: {'✅' if sms_success else '❌'}")
    print(f"💬 WhatsApp invitation: {'✅' if whatsapp_success else '❌'}")
    
    return email_success and sms_success and whatsapp_success

async def test_reminder_methods():
    """Test reminder methods for all channels"""
    print("\n⏰ Testing Activity Reminder Methods...")
    
    notification_service = NotificationService()
    
    # Test activity reminder SMS
    sms_success = await notification_service.send_activity_reminder_sms(
        to_phone="+1234567890",
        to_name="Test User",
        activity_title="Beach Volleyball",
        activity_date="Tomorrow",
        activity_time="3:00 PM",
        venue_name="Santa Monica Beach"
    )
    
    # Test activity reminder WhatsApp
    whatsapp_success = await notification_service.send_activity_reminder_whatsapp(
        to_phone="+1234567890",
        to_name="Test User",
        activity_title="Beach Volleyball",
        activity_date="Tomorrow",
        activity_time="3:00 PM",
        venue_name="Santa Monica Beach"
    )
    
    print(f"📱 SMS reminder: {'✅' if sms_success else '❌'}")
    print(f"💬 WhatsApp reminder: {'✅' if whatsapp_success else '❌'}")
    
    return sms_success and whatsapp_success

async def main():
    """Run all communication integration tests"""
    print("🌞 Sunnyside Communication Integration Tests")
    print("=" * 50)
    
    # Test individual integrations
    email_ok = await test_email_integration()
    sms_ok = await test_sms_integration()
    whatsapp_ok = await test_whatsapp_integration()
    
    # Test specific methods
    invitations_ok = await test_activity_invitation_methods()
    reminders_ok = await test_reminder_methods()
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 30)
    print(f"📧 EmailJS Integration: {'✅ PASS' if email_ok else '❌ FAIL'}")
    print(f"📱 Twilio SMS Integration: {'✅ PASS' if sms_ok else '❌ FAIL'}")
    print(f"💬 Twilio WhatsApp Integration: {'✅ PASS' if whatsapp_ok else '❌ FAIL'}")
    print(f"🎯 Activity Invitations: {'✅ PASS' if invitations_ok else '❌ FAIL'}")
    print(f"⏰ Activity Reminders: {'✅ PASS' if reminders_ok else '❌ FAIL'}")
    
    all_passed = email_ok and sms_ok and whatsapp_ok and invitations_ok and reminders_ok
    
    print(f"\n🏆 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 All communication integrations are working correctly!")
        print("📝 Note: In local development, actual emails/SMS/WhatsApp are simulated.")
        print("🔧 To use real services, configure the appropriate credentials in your .env file.")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())