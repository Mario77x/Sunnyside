from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from bson import ObjectId
from datetime import datetime
import logging

from backend.models.invite import (
    GuestResponseRequest,
    PublicActivityResponse,
    GuestResponseSubmission
)
from backend.models.activity import InviteeResponse
from backend.services.notifications import NotificationService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invites", tags=["invites"])


async def get_database():
    """Dependency to get database connection."""
    import backend.main as main_module
    if main_module.mongodb_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    return main_module.mongodb_client[main_module.DATABASE_NAME]


async def get_public_activity_data(db: AsyncIOMotorDatabase, activity_id: str) -> Optional[dict]:
    """Fetch activity data for public viewing (guests)."""
    if not ObjectId.is_valid(activity_id):
        return None
    
    activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
    if not activity:
        return None
    
    # Get organizer name
    organizer = await db.users.find_one({"_id": activity["organizer_id"]})
    organizer_name = organizer["name"] if organizer else "Unknown"
    
    return {
        "activity": activity,
        "organizer_name": organizer_name
    }


async def update_invitee_response(
    db: AsyncIOMotorDatabase, 
    activity_id: str, 
    guest_id: str, 
    response_data: GuestResponseRequest
) -> bool:
    """Update a specific invitee's response within an activity document."""
    if not ObjectId.is_valid(activity_id):
        return False
    
    # Find the activity and the specific invitee
    activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
    if not activity:
        return False
    
    # Find the invitee by guest_id (which could be email or a unique identifier)
    invitee_found = False
    for i, invitee in enumerate(activity.get("invitees", [])):
        # Match by guest_id (could be email or ObjectId string)
        if (invitee.get("email") == guest_id or 
            str(invitee.get("id", "")) == guest_id):
            invitee_found = True
            break
    
    if not invitee_found:
        return False
    
    # Update the specific invitee's response using email match
    update_result = await db.activities.update_one(
        {
            "_id": ObjectId(activity_id),
            "invitees.email": guest_id
        },
        {
            "$set": {
                "invitees.$.response": response_data.response.value,
                "invitees.$.availability_note": response_data.availability_note,
                "invitees.$.preferences": response_data.preferences or {},
                "invitees.$.venue_suggestion": response_data.venue_suggestion,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return update_result.modified_count > 0


@router.get("/{activity_id}", response_model=PublicActivityResponse)
async def get_public_activity(
    activity_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get public activity details for guests.
    
    This endpoint does not require authentication and returns a simplified
    version of the activity data suitable for guests to view.
    """
    try:
        # Get activity data
        activity_data = await get_public_activity_data(db, activity_id)
        if not activity_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        activity = activity_data["activity"]
        organizer_name = activity_data["organizer_name"]
        
        # Return public activity response
        return PublicActivityResponse(
            id=str(activity["_id"]),
            title=activity["title"],
            description=activity.get("description"),
            organizer_name=organizer_name,
            selected_date=activity.get("selected_date"),
            selected_days=activity.get("selected_days", []),
            activity_type=activity.get("activity_type"),
            weather_preference=activity.get("weather_preference"),
            timeframe=activity.get("timeframe"),
            group_size=activity.get("group_size")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity: {str(e)}"
        )


@router.post("/{activity_id}/respond", response_model=GuestResponseSubmission)
async def submit_guest_response(
    activity_id: str,
    response_data: GuestResponseRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Submit a guest response to an activity invitation.
    
    This endpoint does not require authentication. The guest is identified
    by the guest_id in the request body (typically their email).
    """
    try:
        # Validate that activity exists
        activity_data = await get_public_activity_data(db, activity_id)
        if not activity_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Ensure guest_id is provided
        if not response_data.guest_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guest identifier is required"
            )
        
        # Update the invitee's response
        success = await update_invitee_response(
            db, activity_id, response_data.guest_id, response_data
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest not found in activity invitees or response could not be updated"
            )
        
        # Find the guest name for response
        activity = activity_data["activity"]
        guest_name = None
        for invitee in activity.get("invitees", []):
            if (invitee.get("email") == response_data.guest_id or
                str(invitee.get("id", "")) == response_data.guest_id):
                guest_name = invitee.get("name")
                break
        
        # Send notification to organizer (THIS WAS MISSING!)
        logger.info(f"Sending notification to organizer for guest response from {guest_name}")
        notification_service = NotificationService()
        organizer = await db.users.find_one({"_id": activity["organizer_id"]})
        
        if organizer:
            # Create in-app notification
            await notification_service.create_notification(
                db,
                str(activity["organizer_id"]),
                f"{guest_name} responded '{response_data.response.value}' to {activity['title']}",
                "activity_response",
                {
                    "activity_id": activity_id,
                    "activity_title": activity["title"],
                    "responder_name": guest_name,
                    "response": response_data.response.value,
                    "availability_note": response_data.availability_note,
                    "venue_suggestion": response_data.venue_suggestion
                }
            )
            
            # Send email notification to organizer
            email_sent = await notification_service.send_activity_response_notification_email(
                to_email=organizer["email"],
                to_name=organizer["name"],
                responder_name=guest_name or "Guest",
                activity_title=activity["title"],
                response=response_data.response.value,
                availability_note=response_data.availability_note,
                venue_suggestion=response_data.venue_suggestion
            )
            
            logger.info(f"Notification sent to organizer {organizer['name']} - Email: {email_sent}")
        else:
            logger.error(f"Could not find organizer for activity {activity_id}")
        
        return GuestResponseSubmission(
            message="Response submitted successfully",
            response_recorded=response_data.response,
            guest_name=guest_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit response: {str(e)}"
        )