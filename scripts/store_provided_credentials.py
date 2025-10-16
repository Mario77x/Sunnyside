#!/usr/bin/env python3
"""
Store the provided credentials in MongoDB using the secrets management system.
This script stores all the actual credentials provided by the user.
"""

import asyncio
import sys
from secrets_manager import SecretsManager

# PLACEHOLDER - Actual credentials should be provided via environment variables or secure input
# This script template shows the structure for credential storage
CREDENTIALS = {
    # EmailJS credentials
    "EMAILJS_PUBLIC_KEY": "[REPLACE_WITH_ACTUAL_PUBLIC_KEY]",
    "EMAILJS_SERVICE_ID": "[REPLACE_WITH_ACTUAL_SERVICE_ID]",
    
    # EmailJS Template IDs (provided by user)
    "EMAILJS_PASSWORD_RESET_TEMPLATE_ID": "[REPLACE_WITH_ACTUAL_TEMPLATE_ID]",
    "EMAILJS_ACTIVITY_RESPONSE_TEMPLATE_ID": "[REPLACE_WITH_ACTUAL_TEMPLATE_ID]",
    "EMAILJS_ACTIVITY_CANCELLATION_TEMPLATE_ID": "[REPLACE_WITH_ACTUAL_TEMPLATE_ID]",
    "EMAILJS_UPCOMING_ACTIVITY_REMINDER_TEMPLATE_ID": "[REPLACE_WITH_ACTUAL_TEMPLATE_ID]",
    "EMAILJS_ACTIVITY_INVITATION_TEMPLATE_ID": "[REPLACE_WITH_ACTUAL_TEMPLATE_ID]",
    
    # Twilio credentials
    "TWILIO_ACCOUNT_SID": "[REPLACE_WITH_ACTUAL_ACCOUNT_SID]",
    "TWILIO_AUTH_TOKEN": "[REPLACE_WITH_ACTUAL_AUTH_TOKEN]",
    "TWILIO_PHONE_NUMBER": "[REPLACE_WITH_ACTUAL_PHONE_NUMBER]",
    
    # Mistral AI API Key
    "MISTRAL_API_KEY": "[REPLACE_WITH_ACTUAL_API_KEY]",
}

async def store_all_credentials(environment="development"):
    """Store all provided credentials in MongoDB."""
    manager = SecretsManager()
    
    try:
        await manager.connect()
        print(f"\n🔐 Storing provided credentials in MongoDB...")
        print(f"Environment: {environment}")
        print("=" * 60)
        
        success_count = 0
        total_count = len(CREDENTIALS)
        
        for key, value in CREDENTIALS.items():
            print(f"Storing {key}...")
            success = await manager.set_secret(key, value, environment)
            if success:
                success_count += 1
            else:
                print(f"❌ Failed to store {key}")
        
        print("\n" + "=" * 60)
        print(f"✅ Successfully stored {success_count}/{total_count} credentials")
        
        if success_count == total_count:
            print("🎉 All credentials stored successfully!")
        else:
            print(f"⚠️  {total_count - success_count} credentials failed to store")
        
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ Error storing credentials: {e}")
        return False
    finally:
        await manager.disconnect()

async def verify_stored_credentials(environment="development"):
    """Verify that all credentials were stored correctly."""
    manager = SecretsManager()
    
    try:
        await manager.connect()
        print(f"\n🔍 Verifying stored credentials...")
        print("=" * 60)
        
        verification_results = {}
        
        for key in CREDENTIALS.keys():
            stored_value = await manager.get_secret(key, environment)
            if stored_value:
                # Verify the value matches (show only first/last few chars for security)
                original_value = CREDENTIALS[key]
                if stored_value == original_value:
                    verification_results[key] = "✅ VERIFIED"
                    print(f"✅ {key}: Verified")
                else:
                    verification_results[key] = "❌ MISMATCH"
                    print(f"❌ {key}: Value mismatch")
            else:
                verification_results[key] = "❌ NOT FOUND"
                print(f"❌ {key}: Not found")
        
        print("\n" + "=" * 60)
        verified_count = sum(1 for result in verification_results.values() if "VERIFIED" in result)
        print(f"📊 Verification Summary: {verified_count}/{len(CREDENTIALS)} credentials verified")
        
        return verification_results
        
    except Exception as e:
        print(f"❌ Error verifying credentials: {e}")
        return {}
    finally:
        await manager.disconnect()

async def list_all_secrets(environment="development"):
    """List all secrets in the database."""
    manager = SecretsManager()
    
    try:
        await manager.connect()
        print(f"\n📋 Listing all secrets in environment '{environment}'...")
        await manager.list_secrets(environment)
        
    except Exception as e:
        print(f"❌ Error listing secrets: {e}")
    finally:
        await manager.disconnect()

async def main():
    print("🚀 Sunnyside Credentials Storage Script")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        environment = sys.argv[2] if len(sys.argv) > 2 else "development"
        
        if action == "store":
            success = await store_all_credentials(environment)
            sys.exit(0 if success else 1)
        elif action == "verify":
            results = await verify_stored_credentials(environment)
            verified_count = sum(1 for result in results.values() if "VERIFIED" in result)
            sys.exit(0 if verified_count == len(CREDENTIALS) else 1)
        elif action == "list":
            await list_all_secrets(environment)
            sys.exit(0)
        elif action == "all":
            print("Step 1: Storing credentials...")
            success = await store_all_credentials(environment)
            if success:
                print("\nStep 2: Verifying credentials...")
                results = await verify_stored_credentials(environment)
                print("\nStep 3: Listing all secrets...")
                await list_all_secrets(environment)
                
                verified_count = sum(1 for result in results.values() if "VERIFIED" in result)
                sys.exit(0 if verified_count == len(CREDENTIALS) else 1)
            else:
                sys.exit(1)
        else:
            print("❌ Invalid action. Use: store, verify, list, or all")
            sys.exit(1)
    else:
        print("📋 Available actions:")
        print("  python scripts/store_provided_credentials.py store [environment]  - Store all credentials")
        print("  python scripts/store_provided_credentials.py verify [environment] - Verify stored credentials")
        print("  python scripts/store_provided_credentials.py list [environment]   - List all secrets")
        print("  python scripts/store_provided_credentials.py all [environment]    - Store, verify, and list")
        print(f"\n📊 Credentials to be stored:")
        print(f"   EmailJS: 5 credentials (Public Key, Service ID, 3 Template IDs)")
        print(f"   Twilio:  3 credentials (Account SID, Auth Token, Phone Number)")
        print(f"   Mistral: 1 credential (API Key)")
        print(f"   Total:   {len(CREDENTIALS)} credentials")

if __name__ == "__main__":
    asyncio.run(main())