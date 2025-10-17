#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import bcrypt
from dotenv import load_dotenv

def setup_response_change_test():
    """
    Set up a test scenario for response change modal testing.
    Creates an activity with an existing "YES" response from the test user.
    """
    
    # Load environment variables
    load_dotenv()
    
    # Connect to MongoDB using the same connection as the backend
    MONGODB_URI = os.getenv("MONGODB_URI")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "sunnyside")
    
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI environment variable is required but not set")
    
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    # Collections
    users_collection = db['users']
    activities_collection = db['activities']
    
    print("Setting up response change test scenario...")
    
    # 1. Ensure test user exists
    test_user_email = "test@example.com"
    test_user = users_collection.find_one({"email": test_user_email})
    
    if not test_user:
        print("Creating test user...")
        hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())
        test_user_id = users_collection.insert_one({
            "email": test_user_email,
            "password": hashed_password,
            "name": "Testy user",
            "created_at": datetime.utcnow()
        }).inserted_id
        test_user = users_collection.find_one({"_id": test_user_id})
        print(f"Created test user with ID: {test_user_id}")
    else:
        print(f"Test user already exists with ID: {test_user['_id']}")
    
    # 2. Create test organizer user
    organizer_email = "organizer@example.com"
    organizer_user = users_collection.find_one({"email": organizer_email})
    
    if not organizer_user:
        print("Creating test organizer...")
        hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())
        organizer_user_id = users_collection.insert_one({
            "email": organizer_email,
            "password": hashed_password,
            "name": "Test Organizer",
            "created_at": datetime.utcnow()
        }).inserted_id
        organizer_user = users_collection.find_one({"_id": organizer_user_id})
        print(f"Created organizer user with ID: {organizer_user_id}")
    else:
        print(f"Organizer user already exists with ID: {organizer_user['_id']}")
    
    # 3. Create activity with existing response
    activity_title = "Response Change Test Activity"
    
    # Check if activity already exists
    existing_activity = activities_collection.find_one({
        "title": activity_title,
        "organizer_id": organizer_user['_id']
    })
    
    if existing_activity:
        print(f"Activity already exists with ID: {existing_activity['_id']}")
        activity_id = existing_activity['_id']
    else:
        print("Creating test activity...")
        activity_data = {
            "title": activity_title,
            "description": "This is a test activity for testing response change modal functionality.",
            "organizer_id": organizer_user['_id'],
            "organizer_name": organizer_user['name'],
            "possible_dates": ["Sunday"],
            "weather_preference": "either",
            "activity_date": "Flexible",
            "invitees": [
                {
                    "user_id": test_user['_id'],
                    "email": test_user['email'],
                    "name": test_user['name'],
                    "response": "YES",  # Pre-existing response
                    "responded_at": datetime.utcnow() - timedelta(hours=1),  # Responded 1 hour ago
                    "preferences": {
                        "outdoor_activities": False,
                        "indoor_activities": True,
                        "food_drinks": True,
                        "sports_fitness": False,
                        "culture_arts": False,
                        "nightlife": False,
                        "family_activities": False,
                        "adventure": False
                    },
                    "venue_suggestion": ""
                }
            ],
            "status": "active",
            "created_at": datetime.utcnow() - timedelta(hours=2),  # Created 2 hours ago
            "updated_at": datetime.utcnow() - timedelta(hours=1)   # Updated when response was submitted
        }
        
        activity_id = activities_collection.insert_one(activity_data).inserted_id
        print(f"Created activity with ID: {activity_id}")
    
    # 4. Verify the setup
    activity = activities_collection.find_one({"_id": activity_id})
    test_user_response = None
    
    for invitee in activity.get('invitees', []):
        if invitee.get('user_id') == test_user['_id']:
            test_user_response = invitee.get('response')
            break
    
    print("\n" + "="*50)
    print("RESPONSE CHANGE TEST SETUP COMPLETE")
    print("="*50)
    print(f"Activity ID: {activity_id}")
    print(f"Activity Title: {activity['title']}")
    print(f"Test User: {test_user['email']} (ID: {test_user['_id']})")
    print(f"Current Response: {test_user_response}")
    print(f"Organizer: {organizer_user['email']} (ID: {organizer_user['_id']})")
    print("\nTo test the response change modal:")
    print("1. Login as test@example.com / password123")
    print("2. Go to the 'Invited' tab")
    print(f"3. Click on '{activity_title}'")
    print("4. Change response from 'YES' to 'NO' or 'MAYBE'")
    print("5. The confirmation modal should appear")
    print("6. Confirm the change and verify immediate UI update")
    print("="*50)
    
    client.close()
    return activity_id, test_user['_id']

if __name__ == "__main__":
    setup_response_change_test()