#!/usr/bin/env python3
"""
Google Calendar Setup Verification Script

This script verifies that your Google Calendar integration is properly configured.

Usage:
    python scripts/verify_google_calendar_setup.py
"""

import os
import sys
from pathlib import Path

def check_environment_variables():
    """Check if required environment variables are set."""
    print("🔍 Checking Environment Variables...")
    
    required_vars = {
        'GOOGLE_CLIENT_ID': 'Google OAuth Client ID',
        'GOOGLE_CLIENT_SECRET': 'Google OAuth Client Secret', 
        'GOOGLE_REDIRECT_URI': 'OAuth Redirect URI'
    }
    
    results = {}
    all_set = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values for display
            if 'SECRET' in var:
                display_value = f"{'*' * (len(value) - 4)}{value[-4:]}" if len(value) > 4 else "***"
            else:
                display_value = value
            
            print(f"  ✅ {var}: {display_value}")
            results[var] = True
        else:
            print(f"  ❌ {var}: NOT SET ({description})")
            results[var] = False
            all_set = False
    
    return all_set, results

def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n🔍 Checking Python Dependencies...")
    
    required_packages = [
        ('google.auth', 'google-auth'),
        ('google_auth_oauthlib', 'google-auth-oauthlib'),
        ('google.auth.transport.requests', 'google-auth-httplib2'),
        ('googleapiclient', 'google-api-python-client'),
        ('dotenv', 'python-dotenv')
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}: Installed")
        except ImportError:
            print(f"  ❌ {package_name}: Missing")
            missing_packages.append(package_name)
    
    return len(missing_packages) == 0, missing_packages

def check_google_calendar_service():
    """Check if the Google Calendar service is properly initialized."""
    print("\n🔍 Checking Google Calendar Service...")
    
    try:
        # Add project root to path
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        sys.path.insert(0, str(project_root))
        
        from backend.services.google_calendar import google_calendar_service
        
        if google_calendar_service.enabled:
            print("  ✅ Google Calendar service is enabled")
            
            # Check if client config is properly set
            if hasattr(google_calendar_service, 'client_config'):
                client_id = google_calendar_service.client_config.get('web', {}).get('client_id')
                if client_id:
                    print(f"  ✅ Client configuration loaded")
                else:
                    print("  ❌ Client configuration missing")
                    return False
            
            return True
        else:
            print("  ❌ Google Calendar service is disabled")
            print("     This usually means missing credentials or dependencies")
            return False
            
    except ImportError as e:
        print(f"  ❌ Cannot import Google Calendar service: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error checking Google Calendar service: {e}")
        return False

def check_env_file():
    """Check if .env file exists and is readable."""
    print("\n🔍 Checking .env File...")
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print(f"  ❌ .env file not found at {env_file}")
        return False
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            
        print(f"  ✅ .env file found at {env_file}")
        
        # Check if Google Calendar variables are present
        google_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REDIRECT_URI']
        found_vars = []
        
        for var in google_vars:
            if f"{var}=" in content:
                found_vars.append(var)
        
        if found_vars:
            print(f"  ✅ Found Google Calendar variables: {', '.join(found_vars)}")
        else:
            print("  ⚠️  No Google Calendar variables found in .env file")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading .env file: {e}")
        return False

def test_api_endpoint():
    """Test if the API endpoint is accessible."""
    print("\n🔍 Testing API Endpoint...")
    
    try:
        import requests
        
        # Test the calendar auth endpoint (should return 401 without auth, but not 503)
        response = requests.get("http://localhost:8000/api/v1/calendar/auth/google", timeout=5)
        
        if response.status_code == 503:
            print("  ❌ API returns 503 Service Unavailable")
            print("     This confirms the Google Calendar integration is not configured")
            return False
        elif response.status_code == 401:
            print("  ✅ API is accessible (returns 401 Unauthorized as expected without auth)")
            return True
        else:
            print(f"  ⚠️  API returned unexpected status code: {response.status_code}")
            return True
            
    except requests.exceptions.ConnectionError:
        print("  ⚠️  Cannot connect to backend server")
        print("     Make sure your backend is running on http://localhost:8000")
        return None
    except ImportError:
        print("  ⚠️  'requests' package not available for API testing")
        return None
    except Exception as e:
        print(f"  ❌ Error testing API endpoint: {e}")
        return None

def provide_recommendations(env_check, deps_check, service_check, missing_packages):
    """Provide recommendations based on check results."""
    print("\n" + "=" * 60)
    print("📋 RECOMMENDATIONS")
    print("=" * 60)
    
    if not env_check:
        print("\n🔧 Environment Variables Issue:")
        print("   1. Run: python scripts/setup_google_calendar.py")
        print("   2. Or manually add credentials to your .env file:")
        print("      GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com")
        print("      GOOGLE_CLIENT_SECRET=your-client-secret")
        print("      GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/calendar/auth/google/callback")
    
    if not deps_check:
        print("\n🔧 Missing Dependencies:")
        print(f"   pip install {' '.join(missing_packages)}")
    
    if not service_check:
        print("\n🔧 Service Configuration Issue:")
        print("   1. Ensure environment variables are set correctly")
        print("   2. Restart your backend server")
        print("   3. Check backend logs for specific error messages")
    
    print("\n📚 Additional Resources:")
    print("   • Full setup guide: GOOGLE_CALENDAR_SETUP.md")
    print("   • Google Cloud Console: https://console.cloud.google.com/apis/credentials")
    print("   • Quick setup: python scripts/setup_google_calendar.py")

def main():
    print("🔍 Google Calendar Integration Verification")
    print("=" * 60)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        env_file = project_root / ".env"
        load_dotenv(env_file)
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment variables only")
    
    # Run all checks
    env_file_check = check_env_file()
    env_check, env_results = check_environment_variables()
    deps_check, missing_packages = check_dependencies()
    service_check = check_google_calendar_service()
    api_check = test_api_endpoint()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    checks = [
        ("Environment File", env_file_check),
        ("Environment Variables", env_check),
        ("Python Dependencies", deps_check),
        ("Google Calendar Service", service_check),
        ("API Endpoint", api_check)
    ]
    
    for check_name, result in checks:
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP"
        
        print(f"  {status} {check_name}")
    
    # Overall status
    critical_checks = [env_check, deps_check, service_check]
    if all(critical_checks):
        print("\n🎉 SUCCESS: Google Calendar integration is properly configured!")
        print("   You can now use the calendar features in your application.")
    else:
        print("\n❌ ISSUES FOUND: Google Calendar integration needs attention.")
        provide_recommendations(env_check, deps_check, service_check, missing_packages)
    
    return all(critical_checks)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Verification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during verification: {e}")
        sys.exit(1)