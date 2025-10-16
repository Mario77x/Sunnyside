#!/usr/bin/env python3
"""
Simple Secrets Manager for MongoDB-based secrets storage.

This script provides a command-line interface for managing secrets stored in MongoDB.
It handles encryption/decryption of secret values and provides CRUD operations.
"""

import os
import sys
import argparse
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import base64
import hashlib

# Load environment variables
load_dotenv()

class SecretsManager:
    def __init__(self):
        self.mongodb_uri = os.getenv("MONGODB_URI")
        self.database_name = os.getenv("DATABASE_NAME", "sunnyside")
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secrets."""
        # Try to get key from environment first
        key_env = os.getenv("SECRETS_ENCRYPTION_KEY")
        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env.encode())
            except Exception:
                pass
        
        # Generate key from a combination of environment variables
        # This ensures the same key is generated consistently
        seed_data = (
            os.getenv("MONGODB_URI", "") +
            os.getenv("DATABASE_NAME", "sunnyside") +
            "sunnyside_secrets_key"
        )
        
        # Create a deterministic key from the seed
        key_hash = hashlib.sha256(seed_data.encode()).digest()
        return base64.urlsafe_b64encode(key_hash)
    
    async def connect(self):
        """Connect to MongoDB."""
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable is required")
        
        self.client = AsyncIOMotorClient(self.mongodb_uri)
        self.db = self.client[self.database_name]
        
        # Test connection
        try:
            await self.client.admin.command('ping')
            print("✓ Connected to MongoDB")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt a secret value."""
        return self.cipher.encrypt(value.encode()).decode()
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a secret value."""
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    async def set_secret(self, key: str, value: str, environment: str = "development") -> bool:
        """Set or update a secret."""
        try:
            encrypted_value = self._encrypt_value(value)
            
            # Upsert the secret
            result = await self.db.secrets.update_one(
                {"key": key, "environment": environment},
                {
                    "$set": {
                        "value": encrypted_value,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            action = "Updated" if result.matched_count > 0 else "Created"
            print(f"✓ {action} secret '{key}' for environment '{environment}'")
            return True
            
        except Exception as e:
            print(f"✗ Failed to set secret '{key}': {e}")
            return False
    
    async def get_secret(self, key: str, environment: str = "development") -> Optional[str]:
        """Get a secret value."""
        try:
            document = await self.db.secrets.find_one({
                "key": key,
                "environment": environment
            })
            
            if not document:
                print(f"✗ Secret '{key}' not found for environment '{environment}'")
                return None
            
            decrypted_value = self._decrypt_value(document["value"])
            print(f"✓ Retrieved secret '{key}' for environment '{environment}'")
            return decrypted_value
            
        except Exception as e:
            print(f"✗ Failed to get secret '{key}': {e}")
            return None
    
    async def delete_secret(self, key: str, environment: str = "development") -> bool:
        """Delete a secret."""
        try:
            result = await self.db.secrets.delete_one({
                "key": key,
                "environment": environment
            })
            
            if result.deleted_count > 0:
                print(f"✓ Deleted secret '{key}' for environment '{environment}'")
                return True
            else:
                print(f"✗ Secret '{key}' not found for environment '{environment}'")
                return False
                
        except Exception as e:
            print(f"✗ Failed to delete secret '{key}': {e}")
            return False
    
    async def list_secrets(self, environment: str = "development") -> Dict[str, Any]:
        """List all secrets for an environment (without values)."""
        try:
            cursor = self.db.secrets.find(
                {"environment": environment},
                {"key": 1, "created_at": 1, "updated_at": 1, "_id": 0}
            ).sort("key", 1)
            
            secrets = await cursor.to_list(length=None)
            
            print(f"✓ Found {len(secrets)} secrets for environment '{environment}':")
            for secret in secrets:
                created = secret.get("created_at", "Unknown")
                updated = secret.get("updated_at", "Unknown")
                print(f"  - {secret['key']} (created: {created}, updated: {updated})")
            
            return {"environment": environment, "secrets": secrets}
            
        except Exception as e:
            print(f"✗ Failed to list secrets: {e}")
            return {"environment": environment, "secrets": []}


async def main():
    parser = argparse.ArgumentParser(description="MongoDB Secrets Manager")
    parser.add_argument("action", choices=["set", "get", "delete", "list"], 
                       help="Action to perform")
    parser.add_argument("key", nargs="?", help="Secret key")
    parser.add_argument("value", nargs="?", help="Secret value (for set action)")
    parser.add_argument("--environment", "-e", default="development",
                       help="Environment (default: development)")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.action in ["set", "get", "delete"] and not args.key:
        print("✗ Key is required for this action")
        sys.exit(1)
    
    if args.action == "set" and not args.value:
        print("✗ Value is required for set action")
        sys.exit(1)
    
    # Initialize secrets manager
    manager = SecretsManager()
    
    try:
        await manager.connect()
        
        if args.action == "set":
            success = await manager.set_secret(args.key, args.value, args.environment)
            sys.exit(0 if success else 1)
            
        elif args.action == "get":
            value = await manager.get_secret(args.key, args.environment)
            if value is not None:
                print(f"{args.key}={value}")
                sys.exit(0)
            else:
                sys.exit(1)
                
        elif args.action == "delete":
            success = await manager.delete_secret(args.key, args.environment)
            sys.exit(0 if success else 1)
            
        elif args.action == "list":
            await manager.list_secrets(args.environment)
            sys.exit(0)
            
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
        
    finally:
        await manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())