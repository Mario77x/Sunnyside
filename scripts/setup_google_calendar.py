#!/usr/bin/env python3
"""
Google Calendar Quick Setup Script

This script helps you quickly set up Google Calendar integration by:
1. Prompting for your Google Cloud credentials
2. Adding them to your .env file
3. Verifying the setup

Usage:
    python scripts/setup_google_calendar.py
"""

import os
import sys
from pathlib import Path

def main():
    print("🚀 Google Calendar Integration Setup")
    print("=" * 50)
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    env_file = project_root / ".env"
    
    print(f"Project root: {project_root}")
    print(f"Environment file: {env_file}")
    
    # Check if .env file exists
    if not env_file.exists():
        print("❌ .env file not found!")
        print(f"Please create a .env file in {project_root}")
        return False
    
    print("\n📋 You'll need the following from Google Cloud Console:")
    print("1. Client ID (ends with .apps.googleusercontent.com)")
    print("2. Client Secret")
    print("\n💡 Get these from: https://console.cloud.google.com/apis/credentials")
    print("   → Select your project → OAuth 2.0 Client IDs → Your web client")
    
    # Get user input
    print("\n" + "=" * 50)
    client_id = input("Enter your Google Client ID: ").strip()
    
    if not client_id:
        print("❌ Client ID is required!")
        return False
    
    if not client_id.endswith('.apps.googleusercontent.com'):
        print("⚠️  Warning: Client ID should end with '.apps.googleusercontent.com'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            return False
    
    client_secret = input("Enter your Google Client Secret: ").strip()
    
    if not client_secret:
        print("❌ Client Secret is required!")
        return False
    
    # Default redirect URI
    redirect_uri = "http://localhost:8000/api/v1/calendar/auth/google/callback"
    custom_redirect = input(f"Redirect URI (press Enter for default: {redirect_uri}): ").strip()
    if custom_redirect:
        redirect_uri = custom_redirect
    
    # Read existing .env file
    env_lines = []
    google_vars = {
        'GOOGLE_CLIENT_ID': client_id,
        'GOOGLE_CLIENT_SECRET': client_secret,
        'GOOGLE_REDIRECT_URI': redirect_uri
    }
    
    # Read existing content
    with open(env_file, 'r') as f:
        env_lines = f.readlines()
    
    # Remove existing Google Calendar variables
    env_lines = [line for line in env_lines if not any(line.startswith(var) for var in google_vars.keys())]
    
    # Add Google Calendar section
    if env_lines and not env_lines[-1].endswith('\n'):
        env_lines.append('\n')
    
    env_lines.append('\n# Google Calendar Integration\n')
    for var, value in google_vars.items():
        env_lines.append(f'{var}={value}\n')
    
    # Write back to file
    try:
        with open(env_file, 'w') as f:
            f.writelines(env_lines)
        print("\n✅ Environment variables added successfully!")
    except Exception as e:
        print(f"❌ Error writing to .env file: {e}")
        return False
    
    # Verify the setup
    print("\n🔍 Verifying setup...")
    
    # Reload environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    # Check if variables are set
    verification_results = []
    for var in google_vars.keys():
        value = os.getenv(var)
        if value:
            verification_results.append(f"✅ {var}: {'*' * (len(value) - 10) + value[-10:] if len(value) > 10 else '***'}")
        else:
            verification_results.append(f"❌ {var}: NOT SET")
    
    print("\n📊 Verification Results:")
    for result in verification_results:
        print(f"  {result}")
    
    # Test Google Calendar service
    try:
        sys.path.append(str(project_root))
        from backend.services.google_calendar import google_calendar_service
        
        if google_calendar_service.enabled:
            print("✅ Google Calendar service is enabled and ready!")
        else:
            print("❌ Google Calendar service is not enabled")
            print("   This might be due to missing dependencies or configuration issues")
    except ImportError as e:
        print(f"⚠️  Could not import Google Calendar service: {e}")
        print("   Make sure you've installed the required dependencies:")
        print("   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    except Exception as e:
        print(f"⚠️  Error checking Google Calendar service: {e}")
    
    print("\n🎉 Setup Complete!")
    print("\n📝 Next Steps:")
    print("1. Restart your backend server if it's running")
    print("2. Test the integration by visiting: http://localhost:8000/api/v1/calendar/auth/google")
    print("3. Check the full setup guide: GOOGLE_CALENDAR_SETUP.md")
    
    print("\n🔧 Troubleshooting:")
    print("- If you get 'redirect_uri_mismatch', check your Google Cloud Console redirect URIs")
    print("- If you get 'access_denied', make sure you're added as a test user")
    print("- Run 'python scripts/verify_google_calendar_setup.py' for detailed diagnostics")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)