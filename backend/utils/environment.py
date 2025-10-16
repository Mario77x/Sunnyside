import os
import asyncio
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorClient
from cryptography.fernet import Fernet
import base64
import hashlib


def is_local_development() -> bool:
    """
    Determine if the application is running in local development environment.
    
    Returns:
        bool: True if running locally, False otherwise
    """
    # Check common development environment indicators
    environment = os.getenv("ENVIRONMENT", "").lower()
    if environment in ["development", "dev", "local"]:
        return True
    
    # Check if running on localhost/127.0.0.1
    host = os.getenv("HOST", "").lower()
    if "localhost" in host or "127.0.0.1" in host:
        return True
    
    # Check for development server indicators
    if os.getenv("DEBUG", "").lower() in ["true", "1"]:
        return True
    
    # Check if FRONTEND_URL contains localhost
    frontend_url = os.getenv("FRONTEND_URL", "")
    if "localhost" in frontend_url or "127.0.0.1" in frontend_url:
        return True
    
    # Default to False for production safety
    return False


def get_frontend_url() -> str:
    """
    Get the appropriate frontend URL based on environment.
    
    Returns:
        str: Frontend URL (localhost for development, production URL otherwise)
    """
    if is_local_development():
        # Temporary solution, sending links to local env during PoC testing, to be removed before launch
        return "http://localhost:5137"
    
    return os.getenv("FRONTEND_URL", "https://sunnyside.app")


def get_invite_link(activity_id: str, guest_email: Optional[str] = None) -> str:
    """
    Generate an invite link for an activity.
    
    Args:
        activity_id: The ID of the activity
        guest_email: Optional guest email for personalized links
        
    Returns:
        str: Complete invite link
    """
    base_url = get_frontend_url()
    invite_path = f"/guest?activity={activity_id}"
    
    if guest_email:
        invite_path += f"&email={guest_email}"
    
    return f"{base_url}{invite_path}"


def get_signup_link(invitation_token: Optional[str] = None) -> str:
    """
    Generate a signup link.
    
    Args:
        invitation_token: Optional invitation token
        
    Returns:
        str: Complete signup link
    """
    base_url = get_frontend_url()
    signup_path = "/signup"
    
    if invitation_token:
        signup_path += f"?token={invitation_token}"
    
    return f"{base_url}{signup_path}"


class SecretsLoader:
    """Utility class for loading secrets from MongoDB."""
    
    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key) if self.encryption_key else None
        
    def _get_encryption_key(self) -> Optional[bytes]:
        """Get encryption key for secrets."""
        try:
            # Try to get key from environment first
            key_env = os.getenv("SECRETS_ENCRYPTION_KEY")
            if key_env:
                return base64.urlsafe_b64decode(key_env.encode())
            
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
        except Exception:
            return None
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a secret value."""
        if not self.cipher:
            raise ValueError("Encryption key not available")
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    async def load_secrets_from_db(self, mongodb_client: AsyncIOMotorClient,
                                 database_name: str, environment: str = None) -> Dict[str, str]:
        """Load secrets from MongoDB and return as dictionary."""
        secrets = {}
        
        if not mongodb_client:
            print("⚠ MongoDB client not available, skipping secrets loading")
            return secrets
        
        try:
            # Determine environment
            if not environment:
                environment = os.getenv("ENVIRONMENT", "development").lower()
                if environment not in ["development", "production", "staging"]:
                    environment = "development"
            
            # Get database and collection
            db = mongodb_client[database_name]
            collection = db.secrets
            
            # Fetch secrets for the environment
            cursor = collection.find({"environment": environment})
            documents = await cursor.to_list(length=None)
            
            # Decrypt and load secrets
            for doc in documents:
                try:
                    key = doc.get("key")
                    encrypted_value = doc.get("value")
                    
                    if key and encrypted_value:
                        decrypted_value = self._decrypt_value(encrypted_value)
                        secrets[key] = decrypted_value
                        
                except Exception as e:
                    print(f"⚠ Failed to decrypt secret '{key}': {e}")
                    continue
            
            if secrets:
                print(f"✓ Loaded {len(secrets)} secrets from MongoDB for environment '{environment}'")
            else:
                print(f"ℹ No secrets found in MongoDB for environment '{environment}'")
                
        except Exception as e:
            print(f"⚠ Failed to load secrets from MongoDB: {e}")
        
        return secrets


async def load_secrets_from_mongodb(mongodb_client: AsyncIOMotorClient,
                                  database_name: str, environment: str = None) -> None:
    """
    Load secrets from MongoDB and set them as environment variables.
    
    Args:
        mongodb_client: MongoDB client instance
        database_name: Name of the database
        environment: Environment to load secrets for (defaults to ENVIRONMENT env var)
    """
    loader = SecretsLoader()
    secrets = await loader.load_secrets_from_db(mongodb_client, database_name, environment)
    
    # Set secrets as environment variables
    for key, value in secrets.items():
        os.environ[key] = value