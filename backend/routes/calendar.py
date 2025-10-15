from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timedelta
from typing import Optional
import logging

from backend.auth import get_current_user, security
from backend.services.google_calendar import google_calendar_service
from backend.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


async def get_database():
    """Dependency to get database connection."""
    import backend.main as main_module
    if main_module.mongodb_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    return main_module.mongodb_client[main_module.DATABASE_NAME]


@router.get("/auth/google")
async def initiate_google_calendar_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Initiate Google Calendar OAuth2 authentication flow."""
    try:
        # Verify user is authenticated
        current_user = await get_current_user(credentials, db)
        
        # Generate state parameter with user ID for security
        state = f"user_{current_user.id}"
        
        # Get authorization URL
        auth_url = google_calendar_service.get_authorization_url(state=state)
        
        return {"authorization_url": auth_url}
        
    except Exception as e:
        logger.error(f"Error initiating Google Calendar auth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Google Calendar authentication"
        )


@router.get("/auth/google/callback")
async def google_calendar_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter"),
    error: Optional[str] = Query(None, description="Error from Google"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Handle Google Calendar OAuth2 callback."""
    try:
        if error:
            logger.error(f"Google Calendar auth error: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google Calendar authentication failed: {error}"
            )
        
        if not state or not state.startswith("user_"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        # Extract user ID from state
        user_id = state.replace("user_", "")
        
        # Exchange code for tokens
        credentials_dict = google_calendar_service.exchange_code_for_tokens(code, state)
        
        # Update user record with credentials
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "google_calendar_integrated": True,
                    "google_calendar_credentials": credentials_dict
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Redirect to frontend success page
        return RedirectResponse(
            url="/onboarding?calendar_connected=true",
            status_code=status.HTTP_302_FOUND
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Google Calendar callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete Google Calendar authentication"
        )


@router.get("/availability")
async def get_calendar_availability(
    start_date: str = Query(..., description="Start date in ISO format"),
    end_date: str = Query(..., description="End date in ISO format"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get user's calendar availability for the specified date range."""
    try:
        # Verify user is authenticated
        current_user = await get_current_user(credentials, db)
        
        # Check if user has Google Calendar integrated
        if not current_user.google_calendar_integrated or not current_user.google_calendar_credentials:
            return {
                "integrated": False,
                "message": "Google Calendar not integrated"
            }
        
        # Parse dates
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
        
        # Refresh credentials if needed
        credentials_dict = google_calendar_service.refresh_access_token(
            current_user.google_calendar_credentials
        )
        
        # Update credentials in database if they were refreshed
        if credentials_dict != current_user.google_calendar_credentials:
            await db.users.update_one(
                {"_id": ObjectId(current_user.id)},
                {"$set": {"google_calendar_credentials": credentials_dict}}
            )
        
        # Get availability
        availability = google_calendar_service.get_availability(
            credentials_dict, start_dt, end_dt
        )
        
        return {
            "integrated": True,
            "availability": availability
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting calendar availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get calendar availability"
        )


@router.delete("/integration")
async def disconnect_google_calendar(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Disconnect Google Calendar integration."""
    try:
        # Verify user is authenticated
        current_user = await get_current_user(credentials, db)
        
        # Remove Google Calendar integration
        result = await db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {
                "$set": {
                    "google_calendar_integrated": False,
                    "google_calendar_credentials": None
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "Google Calendar integration disconnected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting Google Calendar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Google Calendar integration"
        )


@router.get("/status")
async def get_calendar_integration_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get the current Google Calendar integration status for the user."""
    try:
        # Verify user is authenticated
        current_user = await get_current_user(credentials, db)
        
        return {
            "integrated": current_user.google_calendar_integrated,
            "has_credentials": current_user.google_calendar_credentials is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting calendar status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get calendar integration status"
        )