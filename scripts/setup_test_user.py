#!/usr/bin/env python3
"""
Script to create a test user in the database for development/testing purposes.
This user data is stored locally and should NOT be committed to version control.
"""

import json
import sys
import os
import requests
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def load_test_user_data():
    """Load test user data from test-user.json"""
    test_user_file = Path(__file__).parent.parent / "test-user.json"
    
    if not test_user_file.exists():
        print("❌ test-user.json not found. Please create it first.")
        return None
    
    with open(test_user_file, 'r') as f:
        return json.load(f)

def create_test_user_via_api():
    """Create test user via the API endpoint"""
    user_data = load_test_user_data()
    if not user_data:
        return False
    
    # API endpoint
    api_url = "http://localhost:8000/api/v1/auth/signup"
    
    try:
        response = requests.post(api_url, json=user_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test user created successfully!")
            print(f"   Email: {user_data['email']}")
            print(f"   Name: {user_data['name']}")
            
            # Save the token for future use
            token_file = Path(__file__).parent.parent / "test-user-token.json"
            with open(token_file, 'w') as f:
                json.dump({
                    "access_token": result.get("access_token"),
                    "token_type": result.get("token_type", "bearer"),
                    "user_email": user_data['email']
                }, f, indent=2)
            print(f"   Token saved to: {token_file}")
            return True
            
        elif response.status_code == 400:
            error_detail = response.json().get("detail", "Unknown error")
            if "already registered" in error_detail.lower():
                print("ℹ️  Test user already exists. Attempting to login...")
                return login_test_user()
            else:
                print(f"❌ Failed to create test user: {error_detail}")
                return False
        else:
            print(f"❌ Failed to create test user. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the backend API at http://localhost:8000")
        print("   Make sure the backend server is running.")
        return False
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

def login_test_user():
    """Login with test user credentials"""
    user_data = load_test_user_data()
    if not user_data:
        return False
    
    # API endpoint
    api_url = "http://localhost:8000/api/v1/auth/login"
    
    login_data = {
        "username": user_data["email"],  # API expects 'username' field
        "password": user_data["password"]
    }
    
    try:
        response = requests.post(api_url, json=login_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test user logged in successfully!")
            
            # Save the token for future use
            token_file = Path(__file__).parent.parent / "test-user-token.json"
            with open(token_file, 'w') as f:
                json.dump({
                    "access_token": result.get("access_token"),
                    "token_type": result.get("token_type", "bearer"),
                    "user_email": user_data['email']
                }, f, indent=2)
            print(f"   Token saved to: {token_file}")
            return True
        else:
            print(f"❌ Failed to login test user. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error logging in test user: {e}")
        return False

def main():
    print("🔧 Setting up test user...")
    
    if create_test_user_via_api():
        print("\n✅ Test user setup complete!")
        print("   You can now use this user for testing the frontend.")
        print("   The authentication token has been saved locally.")
    else:
        print("\n❌ Test user setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()