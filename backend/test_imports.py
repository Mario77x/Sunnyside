#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path so we can import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Testing imports...")
    
    print("1. Testing backend.models.user import...")
    from backend.models.user import User, UserCreate, UserLogin, UserResponse, Token
    print("✓ backend.models.user imported successfully")
    
    print("2. Testing backend.auth import...")
    from backend.auth import verify_password, get_password_hash, create_access_token
    print("✓ backend.auth imported successfully")
    
    print("3. Testing backend.routes.auth import...")
    from backend.routes.auth import router
    print("✓ backend.routes.auth imported successfully")
    
    print("4. Testing router endpoints...")
    print(f"Router prefix: {router.prefix}")
    print(f"Router tags: {router.tags}")
    print(f"Number of routes: {len(router.routes)}")
    
    for route in router.routes:
        print(f"  - {route.methods} {route.path}")
    
    print("\nAll imports successful!")
    
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()