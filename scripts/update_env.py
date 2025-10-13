#!/usr/bin/env python3
"""
Script to securely update environment variables.
Usage: python scripts/update_env.py
"""

import os
import sys
from pathlib import Path

def update_mongodb_uri():
    """Update the MONGODB_URI in the .env file"""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    
    print("🔐 Sunnyside Environment Variable Updater")
    print("=" * 50)
    
    # Get the new MongoDB URI from user input
    print("\nPlease enter the new MongoDB URI:")
    print("(Input will be hidden for security)")
    
    try:
        # Try to use getpass for hidden input
        import getpass
        new_uri = getpass.getpass("MONGODB_URI: ")
    except ImportError:
        # Fallback to regular input if getpass is not available
        print("Warning: Input will be visible")
        new_uri = input("MONGODB_URI: ")
    
    if not new_uri.strip():
        print("❌ Error: MongoDB URI cannot be empty")
        return False
    
    # Validate the URI format
    if not new_uri.startswith('mongodb'):
        print("❌ Error: Invalid MongoDB URI format")
        return False
    
    # Read the current .env file
    env_lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_lines = f.readlines()
    
    # Update or add the MONGODB_URI line
    updated = False
    for i, line in enumerate(env_lines):
        if line.startswith('MONGODB_URI='):
            env_lines[i] = f'MONGODB_URI={new_uri}\n'
            updated = True
            break
    
    if not updated:
        env_lines.append(f'MONGODB_URI={new_uri}\n')
    
    # Write the updated .env file
    with open(env_file, 'w') as f:
        f.writelines(env_lines)
    
    print("✅ Successfully updated MONGODB_URI in .env file")
    print("\n🔄 Please restart the backend server to apply changes:")
    print("   Ctrl+C to stop the current server, then restart it")
    
    return True

if __name__ == "__main__":
    try:
        success = update_mongodb_uri()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)