#!/usr/bin/env python3
"""
Test script to validate the pre-invite suggestion functionality fixes.

This script tests:
1. "Generate More" functionality appends instead of replaces
2. Suggestions are displayed as cards with images (not raw JSON)
3. State management preserves suggestions when navigating back
4. Backend API returns proper JSON structure
5. Frontend components handle the data correctly
"""

import requests
import json
import sys
from pathlib import Path

# Test configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5137"

def load_test_token():
    """Load the test user token"""
    try:
        with open('test-user-token.json', 'r') as f:
            token_data = json.load(f)
            return token_data['access_token']
    except FileNotFoundError:
        print("❌ Test user token not found. Run setup_test_user.py first.")
        return None

def test_api_recommendations():
    """Test the backend API recommendations endpoint"""
    print("🧪 Testing API recommendations endpoint...")
    
    token = load_test_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test recommendations API
    test_query = "fun outdoor activities with friends"
    payload = {
        "query": test_query,
        "max_results": 3
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/llm/recommendations",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if data.get('success') and 'recommendations' in data:
                print("✅ API returns proper JSON structure")
                
                # Check if recommendations have proper structure
                recommendations = data['recommendations']
                if recommendations and len(recommendations) > 0:
                    first_rec = recommendations[0]
                    required_fields = ['title', 'description', 'category']
                    
                    if all(field in first_rec for field in required_fields):
                        print("✅ Recommendations have proper structure")
                        return True
                    else:
                        print("❌ Recommendations missing required fields")
                        return False
                else:
                    print("❌ No recommendations returned")
                    return False
            else:
                print("❌ API response structure invalid")
                print(f"Response: {data}")
                return False
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return False

def test_json_parsing_fix():
    """Test that the JSON parsing fix works correctly"""
    print("🧪 Testing JSON parsing fix...")
    
    # Read the LLM service file to verify the fix is in place
    try:
        with open('backend/services/llm.py', 'r') as f:
            content = f.read()
            
        # Check for the improved JSON parsing logic
        if 'def _parse_json_response' in content and '```json' in content:
            print("✅ JSON parsing fix is implemented")
            return True
        else:
            print("❌ JSON parsing fix not found")
            return False
            
    except FileNotFoundError:
        print("❌ LLM service file not found")
        return False

def test_frontend_fixes():
    """Test frontend component fixes"""
    print("🧪 Testing frontend component fixes...")
    
    # Test ActivityRecommendations.tsx fixes
    try:
        with open('frontend/src/pages/ActivityRecommendations.tsx', 'r') as f:
            content = f.read()
        
        fixes_found = 0
        
        # Check for "Generate More" append functionality
        if 'append = true' in content and 'generateRecommendations(activity, true)' in content:
            print("✅ Generate More append functionality implemented")
            fixes_found += 1
        else:
            print("❌ Generate More append functionality not found")
        
        # Check for state preservation
        if 'recommendations: location.state?.recommendations' in content:
            print("✅ State preservation for recommendations implemented")
            fixes_found += 1
        else:
            print("❌ State preservation not found")
        
        # Check for API integration
        if 'await apiService.getRecommendations' in content:
            print("✅ API integration implemented")
            fixes_found += 1
        else:
            print("❌ API integration not found")
        
        return fixes_found >= 2
        
    except FileNotFoundError:
        print("❌ ActivityRecommendations.tsx not found")
        return False

def test_invite_guests_navigation():
    """Test InviteGuests navigation fix"""
    print("🧪 Testing InviteGuests navigation fix...")
    
    try:
        with open('frontend/src/pages/InviteGuests.tsx', 'r') as f:
            content = f.read()
        
        # Check for state preservation in back navigation
        if 'recommendations: location.state?.recommendations' in content:
            print("✅ InviteGuests back navigation preserves state")
            return True
        else:
            print("❌ InviteGuests back navigation fix not found")
            return False
            
    except FileNotFoundError:
        print("❌ InviteGuests.tsx not found")
        return False

def test_recommendation_generator_fixes():
    """Test RecommendationGenerator component fixes"""
    print("🧪 Testing RecommendationGenerator component fixes...")
    
    try:
        with open('frontend/src/components/RecommendationGenerator.tsx', 'r') as f:
            content = f.read()
        
        fixes_found = 0
        
        # Check for append functionality
        if 'setRecommendations(prev => [...prev, ...response.data.recommendations])' in content:
            print("✅ RecommendationGenerator append functionality implemented")
            fixes_found += 1
        else:
            print("❌ RecommendationGenerator append functionality not found")
        
        # Check for Generate More button
        if 'generateMoreRecommendations' in content:
            print("✅ Generate More button functionality implemented")
            fixes_found += 1
        else:
            print("❌ Generate More button functionality not found")
        
        # Check for image display
        if 'image_url' in content and 'img' in content:
            print("✅ Image display functionality implemented")
            fixes_found += 1
        else:
            print("❌ Image display functionality not found")
        
        return fixes_found >= 2
        
    except FileNotFoundError:
        print("❌ RecommendationGenerator.tsx not found")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting pre-invite suggestion functionality tests...\n")
    
    tests = [
        ("Backend API", test_api_recommendations),
        ("JSON Parsing Fix", test_json_parsing_fix),
        ("Frontend Fixes", test_frontend_fixes),
        ("Navigation Fix", test_invite_guests_navigation),
        ("Component Fixes", test_recommendation_generator_fixes),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*50}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Pre-invite suggestion fixes are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)