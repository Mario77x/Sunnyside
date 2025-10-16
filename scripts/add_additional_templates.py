#!/usr/bin/env python3
"""
Add the additional EmailJS template IDs provided by the user.
"""

import asyncio
import sys
from secrets_manager import SecretsManager

# Additional EmailJS template IDs provided by the user
ADDITIONAL_TEMPLATES = {
    "EMAILJS_WELCOME_TEMPLATE_ID": "template_0fpax0t",
    "EMAILJS_CONTACT_REQUEST_TEMPLATE_ID": "template_h9sl1lk", 
    "EMAILJS_CONTACT_ACCEPTED_TEMPLATE_ID": "template_bbrftgt",
}

async def add_additional_templates(environment="development"):
    """Add additional EmailJS template IDs to MongoDB."""
    manager = SecretsManager()
    
    try:
        await manager.connect()
        print(f"\n🔧 Adding additional EmailJS template IDs...")
        print("=" * 60)
        
        success_count = 0
        total_count = len(ADDITIONAL_TEMPLATES)
        
        for key, value in ADDITIONAL_TEMPLATES.items():
            print(f"Adding {key}...")
            success = await manager.set_secret(key, value, environment)
            if success:
                success_count += 1
            else:
                print(f"❌ Failed to add {key}")
        
        print("\n" + "=" * 60)
        print(f"✅ Successfully added {success_count}/{total_count} additional template IDs")
        
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ Error adding templates: {e}")
        return False
    finally:
        await manager.disconnect()

async def main():
    print("🚀 Adding Additional EmailJS Template IDs")
    print("=" * 60)
    
    success = await add_additional_templates()
    
    if success:
        print("\n🎉 All additional template IDs added successfully!")
        print("\n📋 Complete EmailJS Template List:")
        print("1. Welcome > template_0fpax0t")
        print("2. Password Reset > template_bsaapmj") 
        print("3. Activity Invitation > template_du748ku")
        print("4. Activity Response Notification > template_jm0t1cw")
        print("5. Activity Canceled > template_zspn3o6")
        print("6. Upcoming Activity Reminder > template_mlnxnzh")
        print("7. Contact Request > template_h9sl1lk")
        print("8. Contact Request Accepted > template_bbrftgt")
    else:
        print("\n❌ Some template IDs failed to be added")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())