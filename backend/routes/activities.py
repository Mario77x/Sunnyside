from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from bson import ObjectId
from datetime import datetime

from backend.models.activity import (
    Activity,
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    ActivityStatus,
    InviteGuestsRequest,
    Invitee,
    InviteeResponse
)
from backend.models.user import UserResponse
from backend.auth import get_current_user, security
from backend.services.notifications import NotificationService
from backend.utils.environment import get_invite_link

router = APIRouter(prefix="/activities", tags=["activities"])


async def get_database():
    """Dependency to get database connection."""
    import backend.main as main_module
    if main_module.mongodb_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    return main_module.mongodb_client[main_module.DATABASE_NAME]


async def create_activity_in_db(db: AsyncIOMotorDatabase, activity_data: dict) -> dict:
    """Create a new activity in the database."""
    # Set creation and update timestamps
    activity_data["created_at"] = datetime.utcnow()
    activity_data["updated_at"] = datetime.utcnow()
    
    # Insert activity into database
    result = await db.activities.insert_one(activity_data)
    
    # Return the created activity
    activity = await db.activities.find_one({"_id": result.inserted_id})
    return activity


async def get_activities_for_user(db: AsyncIOMotorDatabase, user_id: str) -> List[dict]:
    """Get all activities for a user (both organized and invited)."""
    user_object_id = ObjectId(user_id)
    
    # Find activities where user is organizer OR in invitees list
    cursor = db.activities.find({
        "$or": [
            {"organizer_id": user_object_id},
            {"invitees.id": user_object_id}
        ]
    }).sort("created_at", -1)  # Sort by newest first
    
    activities = await cursor.to_list(length=None)
    return activities


def convert_activity_to_response(activity: dict) -> ActivityResponse:
    """Convert database activity document to ActivityResponse model."""
    return ActivityResponse(
        id=str(activity["_id"]),
        organizer_id=str(activity["organizer_id"]),
        title=activity["title"],
        description=activity.get("description"),
        status=activity.get("status", ActivityStatus.PLANNING),
        timeframe=activity.get("timeframe"),
        group_size=activity.get("group_size"),
        activity_type=activity.get("activity_type"),
        weather_preference=activity.get("weather_preference"),
        selected_date=activity.get("selected_date"),
        selected_days=activity.get("selected_days", []),
        weather_data=activity.get("weather_data", []),
        suggestions=activity.get("suggestions", []),
        invitees=activity.get("invitees", []),
        created_at=activity["created_at"],
        updated_at=activity["updated_at"]
    )


@router.post("", response_model=ActivityResponse)
async def create_activity(
    activity_data: ActivityCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new activity.
    
    The organizer_id is automatically set to the current logged-in user's ID.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Prepare activity data
        activity_dict = activity_data.model_dump(by_alias=True, exclude_unset=True)
        activity_dict["organizer_id"] = ObjectId(current_user.id)
        activity_dict["status"] = ActivityStatus.PLANNING
        
        # Create activity in database
        created_activity = await create_activity_in_db(db, activity_dict)
        
        # Convert to response model
        return convert_activity_to_response(created_activity)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity: {str(e)}"
        )


@router.get("", response_model=List[ActivityResponse])
async def get_user_activities(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all activities for the current user.
    
    Returns both activities they have organized and activities they have been invited to.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Get activities for user
        activities = await get_activities_for_user(db, current_user.id)
        
        # Convert to response models
        return [convert_activity_to_response(activity) for activity in activities]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activities: {str(e)}"
        )


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get a single activity by ID.
    
    User must be either the organizer or an invitee to access the activity.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Validate activity ID
        if not ObjectId.is_valid(activity_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid activity ID"
            )
        
        # Find activity
        activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Check if user has access (organizer or invitee)
        user_object_id = ObjectId(current_user.id)
        has_access = (
            activity["organizer_id"] == user_object_id or
            any(invitee.get("id") == user_object_id for invitee in activity.get("invitees", []))
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this activity"
            )
        
        # Convert to response model
        return convert_activity_to_response(activity)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity: {str(e)}"
        )


@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: str,
    activity_update: ActivityUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update an activity.
    
    Only the organizer can update the activity.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Validate activity ID
        if not ObjectId.is_valid(activity_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid activity ID"
            )
        
        # Find activity
        activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Check if user is the organizer
        if activity["organizer_id"] != ObjectId(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the organizer can update this activity"
            )
        
        # Prepare update data
        update_data = activity_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update activity in database
            await db.activities.update_one(
                {"_id": ObjectId(activity_id)},
                {"$set": update_data}
            )
        
        # Get updated activity
        updated_activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
        
        # Convert to response model
        return convert_activity_to_response(updated_activity)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update activity: {str(e)}"
        )


@router.post("/{activity_id}/invite")
async def invite_guests_to_activity(
    activity_id: str,
    invite_request: InviteGuestsRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Send invitations to guests for an activity.
    
    Only the organizer can invite guests to the activity.
    This endpoint adds invitees to the activity document.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Validate activity ID
        if not ObjectId.is_valid(activity_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid activity ID"
            )
        
        # Find activity
        activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Check if user is the organizer
        if activity["organizer_id"] != ObjectId(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the organizer can invite guests to this activity"
            )
        
        # Prepare invitees list
        new_invitees = []
        existing_emails = {invitee.get("email") for invitee in activity.get("invitees", [])}
        
        for invitee_data in invite_request.invitees:
            email = invitee_data.get("email")
            name = invitee_data.get("name")
            
            if not email or not name:
                continue  # Skip invalid invitee data
            
            # Skip if already invited
            if email in existing_emails:
                continue
            
            # Check if this email belongs to a registered user
            existing_user = await db.users.find_one({"email": email})
            invitee_id = str(existing_user["_id"]) if existing_user else str(ObjectId())
            
            # Create invitee object
            invitee = Invitee(
                id=invitee_id,
                name=name,
                email=email,
                response=InviteeResponse.PENDING,
                availability_note=None,
                venue_suggestion=None
            )
            
            new_invitees.append(invitee.model_dump())
        
        if not new_invitees:
            return {"message": "No new invitees to add"}
        
        # Add new invitees to the activity
        await db.activities.update_one(
            {"_id": ObjectId(activity_id)},
            {
                "$push": {"invitees": {"$each": new_invitees}},
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "status": ActivityStatus.INVITATIONS_SENT
                }
            }
        )
        
        # Send email invitations to all new invitees
        # Temporary solution, sending links to local env during PoC testing, to be removed before launch
        notification_service = NotificationService()
        email_results = []
        
        for invitee in new_invitees:
            # Generate invite link for this specific invitee
            invite_link = get_invite_link(activity_id, invitee["email"])
            
            # Prepare activity details for email
            activity_details = {
                "selected_date": activity.get("selected_date"),
                "selected_days": activity.get("selected_days", []),
                "weather_preference": activity.get("weather_preference"),
                "group_size": activity.get("group_size"),
                "suggestions": activity.get("suggestions", []),
                "weather_data": activity.get("weather_data", [])
            }
            
            # Send email invitation
            email_sent = await notification_service.send_activity_invitation_email(
                to_email=invitee["email"],
                to_name=invitee["name"],
                organizer_name=current_user.name,
                activity_title=activity["title"],
                activity_description=activity.get("description", ""),
                custom_message=invite_request.custom_message,
                invite_link=invite_link,
                activity_details=activity_details
            )
            
            email_results.append({
                "email": invitee["email"],
                "name": invitee["name"],
                "email_sent": email_sent
            })
            
            # Also create in-app notification if the invitee is a registered user
            existing_user = await db.users.find_one({"email": invitee["email"]})
            if existing_user:
                await notification_service.create_notification(
                    db,
                    str(existing_user["_id"]),
                    f"{current_user.name} invited you to {activity['title']}",
                    "activity_invitation",
                    {
                        "activity_id": activity_id,
                        "organizer_name": current_user.name,
                        "activity_title": activity["title"],
                        "invite_link": invite_link
                    }
                )
        
        successful_emails = sum(1 for result in email_results if result["email_sent"])
        
        return {
            "message": "Invitations sent",
            "invited_count": len(new_invitees),
            "emails_sent": successful_emails,
            "custom_message": invite_request.custom_message,
            "email_results": email_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send invitations: {str(e)}"
        )


@router.post("/create-test-invite", response_model=ActivityResponse)
async def create_test_invite(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a test invite where the current user is invited by a mock organizer.
    
    This creates an activity with a mock organizer and adds the current user as an invitee,
    ensuring the activity appears in the user's "invited" list instead of "organized" list.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Create or get a mock organizer user
        mock_organizer_email = "test.organizer@sunnyside.app"
        mock_organizer = await db.users.find_one({"email": mock_organizer_email})
        
        if not mock_organizer:
            # Create mock organizer user
            mock_organizer_data = {
                "name": "Test Organizer",
                "email": mock_organizer_email,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await db.users.insert_one(mock_organizer_data)
            mock_organizer_id = result.inserted_id
        else:
            mock_organizer_id = mock_organizer["_id"]
        
        # Prepare test activity data with mock organizer
        activity_data = {
            "organizer_id": mock_organizer_id,
            "title": "Weekend Brunch",
            "description": "Let's have a nice brunch this Sunday with good food and great company!",
            "status": ActivityStatus.INVITATIONS_SENT,
            "timeframe": "Sunday morning",
            "group_size": "small group",
            "activity_type": "food",
            "weather_preference": "either",
            "selected_days": ["Sunday"],
            "invitees": [
                {
                    "id": current_user.id,
                    "name": current_user.name,
                    "email": current_user.email,
                    "response": InviteeResponse.PENDING.value,
                    "availability_note": None,
                    "venue_suggestion": None,
                    "preferences": {}
                },
                {
                    "id": str(ObjectId()),
                    "name": "Mike Chen",
                    "email": "mike@example.com",
                    "response": InviteeResponse.PENDING.value,
                    "availability_note": None,
                    "venue_suggestion": None,
                    "preferences": {}
                },
                {
                    "id": str(ObjectId()),
                    "name": "Emma Wilson",
                    "email": "emma@example.com",
                    "response": InviteeResponse.PENDING.value,
                    "availability_note": None,
                    "venue_suggestion": None,
                    "preferences": {}
                }
            ]
        }
        
        # Create activity in database
        created_activity = await create_activity_in_db(db, activity_data)
        
        # Convert to response model
        return convert_activity_to_response(created_activity)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test invite: {str(e)}"
        )