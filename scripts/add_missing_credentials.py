#!/usr/bin/env python3
"""
Quick setup script for adding missing communication credentials to MongoDB.
Run this script after obtaining the actual credential values from EmailJS and Twilio.
"""

import asyncio
import sys
from secrets_manager import SecretsManager

# EmailJS credentials that need to be added
EMAILJS_CREDENTIALS = {
    # Core EmailJS configuration
    "EMAILJS_SERVICE_ID": "service_YOUR_SERVICE_ID",  # Replace with actual service ID
    "EMAILJS_PUBLIC_KEY": "user_YOUR_PUBLIC_KEY",     # Replace with actual public key
    
    # EmailJS Template IDs - High Priority (Core Functionality)
    "EMAILJS_ACTIVITY_INVITATION_TEMPLATE_ID": "template_du748ku",  # Already implemented
    "EMAILJS_GUEST_ACTIVITY_INVITATION_TEMPLATE_ID": "template_GUEST_INVITE",
    "EMAILJS_ACTIVITY_RESPONSE_TEMPLATE_ID": "template_jm0t1cw",  # Activity Response Notification
    "EMAILJS_ACTIVITY_FINALIZED_TEMPLATE_ID": "template_FINALIZED",
    
    # EmailJS Template IDs - Medium Priority
    "EMAILJS_WELCOME_TEMPLATE_ID": "template_WELCOME",
    "EMAILJS_CONTACT_REQUEST_TEMPLATE_ID": "template_CONTACT_REQ",
    "EMAILJS_ACCOUNT_INVITATION_TEMPLATE_ID": "template_ACCOUNT_INV",
    "EMAILJS_ACTIVITY_CANCELLATION_TEMPLATE_ID": "template_zspn3o6",  # Activity Canceled
    "EMAILJS_ACTIVITY_RESPONSE_CHANGED_TEMPLATE_ID": "template_RESP_CHANGED",
    "EMAILJS_DEADLINE_REMINDER_TEMPLATE_ID": "template_DEADLINE",
    
    # EmailJS Template IDs - Low Priority (Enhanced Features)
    "EMAILJS_PASSWORD_RESET_TEMPLATE_ID": "template_bsaapmj",  # Password Reset
    "EMAILJS_CONTACT_ACCEPTED_TEMPLATE_ID": "template_CONTACT_ACC",
    "EMAILJS_ACTIVITY_UPDATE_TEMPLATE_ID": "template_UPDATE",
    "EMAILJS_UPCOMING_ACTIVITY_REMINDER_TEMPLATE_ID": "template_mlnxnzh",  # Upcoming Activity Reminder
}

# Twilio credentials that need to be added
TWILIO_CREDENTIALS = {
    "TWILIO_ACCOUNT_SID": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # Replace with actual Account SID
    "TWILIO_AUTH_TOKEN": "your_auth_token_here",              # Replace with actual Auth Token
    "TWILIO_PHONE_NUMBER": "+1234567890",                     # Replace with actual phone number
    "TWILIO_WHATSAPP_NUMBER": "whatsapp:+14155238886",        # Replace with actual WhatsApp number
}

async def add_credentials(credentials_dict, credential_type, environment="development"):
    """Add a set of credentials to MongoDB."""
    manager = SecretsManager()
    
    try:
        await manager.connect()
        print(f"\n🔧 Adding {credential_type} credentials to MongoDB...")
        
        success_count = 0
        total_count = len(credentials_dict)
        
        for key, value in credentials_dict.items():
            if "YOUR_" in value or "xxxxx" in value or "your_" in value:
                print(f"⚠️  Skipping {key} - placeholder value detected. Please update with actual value.")
                continue
                
            success = await manager.set_secret(key, value, environment)
            if success:
                success_count += 1
            else:
                print(f"❌ Failed to add {key}")
        
        print(f"✅ Successfully added {success_count}/{total_count} {credential_type} credentials")
        
    except Exception as e:
        print(f"❌ Error adding {credential_type} credentials: {e}")
    finally:
        await manager.disconnect()

async def main():
    print("🚀 Sunnyside Communication Credentials Setup")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        
        if action == "emailjs":
            await add_credentials(EMAILJS_CREDENTIALS, "EmailJS")
        elif action == "twilio":
            await add_credentials(TWILIO_CREDENTIALS, "Twilio")
        elif action == "all":
            await add_credentials(EMAILJS_CREDENTIALS, "EmailJS")
            await add_credentials(TWILIO_CREDENTIALS, "Twilio")
        else:
            print("❌ Invalid action. Use: emailjs, twilio, or all")
            sys.exit(1)
    else:
        print("📋 Available actions:")
        print("  python scripts/add_missing_credentials.py emailjs  - Add EmailJS credentials")
        print("  python scripts/add_missing_credentials.py twilio   - Add Twilio credentials")
        print("  python scripts/add_missing_credentials.py all      - Add all credentials")
        print("\n⚠️  IMPORTANT: Update the credential values in this script before running!")
        print("   Replace placeholder values with actual credentials from EmailJS and Twilio.")
        
        print(f"\n📊 Current missing credentials:")
        print(f"   EmailJS: {len(EMAILJS_CREDENTIALS)} credentials")
        print(f"   Twilio:  {len(TWILIO_CREDENTIALS)} credentials")
        print(f"   Total:   {len(EMAILJS_CREDENTIALS) + len(TWILIO_CREDENTIALS)} missing credentials")

if __name__ == "__main__":
    asyncio.run(main())