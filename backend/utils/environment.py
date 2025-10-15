import os
from typing import Optional


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