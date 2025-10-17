from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from bson import ObjectId
from datetime import datetime, timedelta

from backend.models.activity import (
    Activity,
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    ActivityStatus,
    InviteGuestsRequest,
    Invitee,
    InviteeResponse,
    UserResponseRequest,
    ActivitySummaryResponse,
    AIRecommendation,
    RecommendationResponse,
    FinalizeActivityRequest,
    FinalizationRecommendationsRequest,
    FinalizationRecommendation,
    FinalizationRecommendationsResponse,
    ActivityFinalizationRequest,
    FinalInvitesRequest,
    CalendarIntegrationRequest
)
from backend.models.user import UserResponse
from backend.auth import get_current_user, security
from backend.services.notifications import NotificationService
from backend.utils.environment import get_invite_link
from backend.dependencies import get_database

router = APIRouter(prefix="/activities", tags=["activities"])


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
    # Note: invitee IDs can be stored as either ObjectId or string, so we check both
    cursor = db.activities.find({
        "$or": [
            {"organizer_id": user_object_id},
            {"invitees.id": user_object_id},  # Check for ObjectId format
            {"invitees.id": user_id}          # Check for string format
        ]
    }).sort("created_at", -1)  # Sort by newest first
    
    activities = await cursor.to_list(length=None)
    return activities


async def convert_activity_to_response(activity: dict, db: AsyncIOMotorDatabase) -> ActivityResponse:
    """Convert database activity document to ActivityResponse model."""
    # Get organizer name
    organizer = await db.users.find_one({"_id": activity["organizer_id"]})
    organizer_name = organizer["name"] if organizer else "Unknown"
    
    return ActivityResponse(
        id=str(activity["_id"]),
        organizer_id=str(activity["organizer_id"]),
        organizer_name=organizer_name,
        title=activity["title"],
        description=activity.get("description"),
        status=activity.get("status", ActivityStatus.PLANNING),
        timeframe=activity.get("timeframe"),
        group_size=activity.get("group_size"),
        activity_type=activity.get("activity_type"),
        weather_preference=activity.get("weather_preference"),
        selected_date=activity.get("selected_date"),
        selected_days=activity.get("selected_days", []),
        deadline=activity.get("deadline"),
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
        return await convert_activity_to_response(created_activity, db)
        
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
        response_activities = []
        for activity in activities:
            response_activity = await convert_activity_to_response(activity, db)
            response_activities.append(response_activity)
        return response_activities
        
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
            any(invitee.get("id") == user_object_id or invitee.get("id") == current_user.id
                for invitee in activity.get("invitees", []))
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this activity"
            )
        
        # Convert to response model
        return await convert_activity_to_response(activity, db)
        
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
        return await convert_activity_to_response(updated_activity, db)
        
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
        
        # Prepare invitees list with user lookup
        new_invitees = []
        invitees_with_user_info = []  # Store invitee data with user lookup results
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
                venue_suggestion=None,
                previous_response=None
            )
            
            new_invitees.append(invitee.model_dump())
            # Store the invitee data along with user info for email processing
            invitees_with_user_info.append({
                "invitee": invitee.model_dump(),
                "existing_user": existing_user
            })
        
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
        
        # Send invitations via selected channel
        notification_service = NotificationService()
        invitation_results = []
        selected_channel = invite_request.channel or "email"  # Default to email
        
        for invitee_info in invitees_with_user_info:
            invitee = invitee_info["invitee"]
            existing_user = invitee_info["existing_user"]
            
            # Generate invite link for this specific invitee
            invite_link = get_invite_link(activity_id, invitee["email"])
            
            # Prepare activity details for invitation
            activity_details = {
                "selected_date": activity.get("selected_date"),
                "selected_days": activity.get("selected_days", []),
                "weather_preference": activity.get("weather_preference"),
                "group_size": activity.get("group_size"),
                "suggestions": activity.get("suggestions", []),
                "weather_data": activity.get("weather_data", [])
            }
            
            invitation_sent = False
            
            # Send invitation based on selected channel
            if selected_channel == "email":
                # Send email invitation - use different functions for registered vs guest users
                if existing_user:
                    # Send invitation to registered user
                    invitation_sent = await notification_service.send_activity_invitation_email(
                        to_email=invitee["email"],
                        to_name=invitee["name"],
                        organizer_name=current_user.name,
                        activity_title=activity["title"],
                        activity_description=activity.get("description", ""),
                        custom_message=invite_request.custom_message,
                        invite_link=invite_link,
                        activity_details=activity_details
                    )
                else:
                    # Send invitation to guest user (non-registered)
                    invitation_sent = await notification_service.send_activity_invitation_email_to_guest(
                        to_email=invitee["email"],
                        to_name=invitee["name"],
                        organizer_name=current_user.name,
                        activity_title=activity["title"],
                        activity_description=activity.get("description", ""),
                        custom_message=invite_request.custom_message,
                        invite_link=invite_link,
                        activity_details=activity_details
                    )
            elif selected_channel == "whatsapp":
                # TODO: Implement WhatsApp invitation sending
                # For now, simulate success
                invitation_sent = True
                print(f"WhatsApp invitation would be sent to {invitee['name']} at {invitee.get('phone', 'no phone')}")
            elif selected_channel == "sms":
                # TODO: Implement SMS invitation sending
                # For now, simulate success
                invitation_sent = True
                print(f"SMS invitation would be sent to {invitee['name']} at {invitee.get('phone', 'no phone')}")
            
            invitation_results.append({
                "email": invitee["email"],
                "name": invitee["name"],
                "channel": selected_channel,
                "invitation_sent": invitation_sent
            })
            
            # Create in-app notification if the invitee is a registered user
            if existing_user:
                await notification_service.create_notification(
                    db,
                    str(existing_user["_id"]),
                    f"{current_user.name} invited you to {activity['title']} via {selected_channel}",
                    "activity_invitation",
                    {
                        "activity_id": activity_id,
                        "organizer_name": current_user.name,
                        "activity_title": activity["title"],
                        "invite_link": invite_link,
                        "channel": selected_channel
                    }
                )
        
        successful_invitations = sum(1 for result in invitation_results if result["invitation_sent"])
        
        # Generate a guest experience link for testing (using the first invitee's email if available)
        guest_experience_link = None
        if new_invitees:
            first_invitee_email = new_invitees[0].get("email")
            if first_invitee_email:
                guest_experience_link = get_invite_link(activity_id, first_invitee_email)
        
        return {
            "message": f"Invitations sent via {selected_channel}",
            "invited_count": len(new_invitees),
            "invitations_sent": successful_invitations,
            "channel": selected_channel,
            "custom_message": invite_request.custom_message,
            "invitation_results": invitation_results,
            "guest_experience_link": guest_experience_link
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
                    "preferences": {},
                    "previous_response": None
                },
                {
                    "id": str(ObjectId()),
                    "name": "Mike Chen",
                    "email": "mike@example.com",
                    "response": InviteeResponse.PENDING.value,
                    "availability_note": None,
                    "venue_suggestion": None,
                    "preferences": {},
                    "previous_response": None
                },
                {
                    "id": str(ObjectId()),
                    "name": "Emma Wilson",
                    "email": "emma@example.com",
                    "response": InviteeResponse.PENDING.value,
                    "availability_note": None,
                    "venue_suggestion": None,
                    "preferences": {},
                    "previous_response": None
                }
            ]
        }
        
        # Create activity in database
        created_activity = await create_activity_in_db(db, activity_data)
        
        # Convert to response model
        return await convert_activity_to_response(created_activity, db)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test invite: {str(e)}"
        )


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete an activity.
    
    Only the organizer can delete the activity.
    
    Conditional logic:
    - If the activity is a draft or in the past: Simply delete from database
    - If the activity has sent invites and is in the future: Delete and notify all invitees
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
                detail="Only the organizer can delete this activity"
            )
        
        # Determine if we need to send notifications
        activity_status = activity.get("status", ActivityStatus.PLANNING)
        selected_date = activity.get("selected_date")
        invitees = activity.get("invitees", [])
        
        # Check if activity is in the future
        is_future_activity = False
        if selected_date:
            try:
                # Handle both datetime objects and ISO strings
                if isinstance(selected_date, str):
                    activity_date = datetime.fromisoformat(selected_date.replace('Z', '+00:00'))
                else:
                    activity_date = selected_date
                is_future_activity = activity_date > datetime.utcnow()
            except:
                # If we can't parse the date, assume it's future to be safe
                is_future_activity = True
        
        # Determine if notifications should be sent
        should_notify = (
            activity_status in [ActivityStatus.INVITATIONS_SENT, ActivityStatus.RESPONSES_COLLECTED, ActivityStatus.FINALIZED] and
            is_future_activity and
            len(invitees) > 0
        )
        
        # Delete the activity from database
        delete_result = await db.activities.delete_one({"_id": ObjectId(activity_id)})
        
        if delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete activity"
            )
        
        # Send cancellation notifications if needed
        notification_results = []
        if should_notify:
            notification_service = NotificationService()
            
            for invitee in invitees:
                invitee_email = invitee.get("email")
                invitee_name = invitee.get("name")
                
                if not invitee_email or not invitee_name:
                    continue
                
                # Send email notification
                email_sent = await notification_service.send_activity_cancellation_email(
                    to_email=invitee_email,
                    to_name=invitee_name,
                    organizer_name=current_user.name,
                    activity_title=activity["title"],
                    activity_description=activity.get("description", ""),
                    cancellation_reason="The organizer has cancelled this activity."
                )
                
                notification_results.append({
                    "email": invitee_email,
                    "name": invitee_name,
                    "email_sent": email_sent
                })
                
                # Also create in-app notification if the invitee is a registered user
                existing_user = await db.users.find_one({"email": invitee_email})
                if existing_user:
                    await notification_service.create_notification(
                        db,
                        str(existing_user["_id"]),
                        f"Activity cancelled: {activity['title']} by {current_user.name}",
                        "activity_cancellation",
                        {
                            "activity_title": activity["title"],
                            "organizer_name": current_user.name,
                            "cancellation_reason": "The organizer has cancelled this activity."
                        }
                    )
        
        # Prepare response
        response_data = {
            "message": "Activity deleted successfully",
            "activity_id": activity_id,
            "activity_title": activity["title"]
        }
        
        if should_notify:
            successful_emails = sum(1 for result in notification_results if result["email_sent"])
            response_data.update({
                "notifications_sent": True,
                "invitees_notified": len(notification_results),
                "emails_sent": successful_emails,
                "notification_results": notification_results
            })
        else:
            response_data["notifications_sent"] = False
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete activity: {str(e)}"
        )


@router.post("/{activity_id}/respond")
async def submit_user_response(
    activity_id: str,
    response_data: UserResponseRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Submit a response to an activity invitation for registered users.
    
    This endpoint requires authentication and allows registered users to respond
    to activities they have been invited to with their availability and preferences.
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
        
        # Check if user is invited to this activity
        user_object_id = ObjectId(current_user.id)
        user_invited = False
        invitee_index = -1
        
        for i, invitee in enumerate(activity.get("invitees", [])):
            if (invitee.get("id") == user_object_id or
                invitee.get("id") == current_user.id or
                invitee.get("email") == current_user.email):
                user_invited = True
                invitee_index = i
                break
        
        if not user_invited:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not invited to this activity"
            )
        
        # Check if this is a response change (user already has a response)
        current_response = activity["invitees"][invitee_index].get("response")
        is_response_change = current_response and current_response != InviteeResponse.PENDING.value
        
        # Store previous response if this is a change
        update_fields = {
            f"invitees.{invitee_index}.response": response_data.response.value,
            f"invitees.{invitee_index}.availability_note": response_data.availability_note,
            f"invitees.{invitee_index}.preferences": response_data.preferences or {},
            f"invitees.{invitee_index}.venue_suggestion": response_data.venue_suggestion,
            "updated_at": datetime.utcnow()
        }
        
        if is_response_change:
            update_fields[f"invitees.{invitee_index}.previous_response"] = current_response
        
        # Update the user's response in the activity
        update_result = await db.activities.update_one(
            {
                "_id": ObjectId(activity_id),
                f"invitees.{invitee_index}.email": current_user.email
            },
            {"$set": update_fields}
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update response"
            )
        
        # Send notification to organizer
        notification_service = NotificationService()
        organizer = await db.users.find_one({"_id": activity["organizer_id"]})
        
        if organizer:
            if is_response_change:
                # Send response change notification
                await notification_service.create_notification(
                    db,
                    str(activity["organizer_id"]),
                    f"{current_user.name} changed their response from '{current_response}' to '{response_data.response.value}' for {activity['title']}",
                    "activity_response_changed",
                    {
                        "activity_id": activity_id,
                        "activity_title": activity["title"],
                        "responder_name": current_user.name,
                        "previous_response": current_response,
                        "new_response": response_data.response.value,
                        "availability_note": response_data.availability_note,
                        "venue_suggestion": response_data.venue_suggestion
                    }
                )
                
                # Send response change email notification
                await notification_service.send_activity_response_changed_notification_email(
                    to_email=organizer["email"],
                    to_name=organizer["name"],
                    responder_name=current_user.name,
                    activity_title=activity["title"],
                    previous_response=current_response,
                    new_response=response_data.response.value,
                    availability_note=response_data.availability_note,
                    venue_suggestion=response_data.venue_suggestion
                )
            else:
                # Send initial response notification
                await notification_service.create_notification(
                    db,
                    str(activity["organizer_id"]),
                    f"{current_user.name} responded '{response_data.response.value}' to {activity['title']}",
                    "activity_response",
                    {
                        "activity_id": activity_id,
                        "activity_title": activity["title"],
                        "responder_name": current_user.name,
                        "response": response_data.response.value,
                        "availability_note": response_data.availability_note,
                        "venue_suggestion": response_data.venue_suggestion
                    }
                )
                
                # Send email notification to organizer
                await notification_service.send_activity_response_notification_email(
                    to_email=organizer["email"],
                    to_name=organizer["name"],
                    responder_name=current_user.name,
                    activity_title=activity["title"],
                    response=response_data.response.value,
                    availability_note=response_data.availability_note,
                    venue_suggestion=response_data.venue_suggestion
                )
        
        return {
            "message": "Response updated successfully" if is_response_change else "Response submitted successfully",
            "response_recorded": response_data.response.value,
            "activity_title": activity["title"],
            "is_change": is_response_change,
            "previous_response": current_response if is_response_change else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit response: {str(e)}"
        )


@router.get("/{activity_id}/summary", response_model=ActivitySummaryResponse)
async def get_activity_summary(
    activity_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get activity summary with all responses.
    
    Only the organizer can access this endpoint. This is typically used
    after the deadline has passed to review all responses.
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
                detail="Only the organizer can view the activity summary"
            )
        
        # Calculate response statistics
        invitees = activity.get("invitees", [])
        total_invitees = len(invitees)
        responses = {
            "yes": 0,
            "no": 0,
            "maybe": 0,
            "pending": 0
        }
        
        venue_suggestions = []
        availability_notes = []
        
        for invitee in invitees:
            response = invitee.get("response", "pending")
            responses[response] = responses.get(response, 0) + 1
            
            if invitee.get("venue_suggestion"):
                venue_suggestions.append({
                    "name": invitee.get("name"),
                    "suggestion": invitee.get("venue_suggestion")
                })
            
            if invitee.get("availability_note"):
                availability_notes.append({
                    "name": invitee.get("name"),
                    "note": invitee.get("availability_note")
                })
        
        # Check if deadline has passed
        deadline_passed = False
        if activity.get("selected_date"):
            try:
                activity_date = activity["selected_date"]
                if isinstance(activity_date, str):
                    activity_date = datetime.fromisoformat(activity_date.replace('Z', '+00:00'))
                # Consider deadline as 24 hours before the activity
                deadline = activity_date - timedelta(hours=24)
                deadline_passed = datetime.utcnow() > deadline
            except:
                deadline_passed = False
        
        return {
            "activity": await convert_activity_to_response(activity, db),
            "summary": {
                "total_invitees": total_invitees,
                "responses": responses,
                "response_rate": round((total_invitees - responses["pending"]) / total_invitees * 100, 1) if total_invitees > 0 else 0,
                "venue_suggestions": venue_suggestions,
                "availability_notes": availability_notes,
                "deadline_passed": deadline_passed
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity summary: {str(e)}"
        )


@router.post("/{activity_id}/recommendations", response_model=RecommendationResponse)
async def generate_ai_recommendations(
    activity_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate AI recommendations based on activity responses.
    
    Only the organizer can request recommendations. This analyzes confirmed
    attendees' preferences and generates personalized venue/activity recommendations.
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
                detail="Only the organizer can request recommendations"
            )
        
        # Analyze responses to get confirmed attendees
        invitees = activity.get("invitees", [])
        confirmed_attendees = [
            invitee for invitee in invitees
            if invitee.get("response") in ["yes", "maybe"]
        ]
        
        if len(confirmed_attendees) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No confirmed attendees to generate recommendations for"
            )
        
        # Collect preferences from confirmed attendees
        preference_counts = {}
        venue_suggestions = []
        
        for attendee in confirmed_attendees:
            # Count preferences
            prefs = attendee.get("preferences", {})
            for pref, value in prefs.items():
                if value:
                    preference_counts[pref] = preference_counts.get(pref, 0) + 1
            
            # Collect venue suggestions
            if attendee.get("venue_suggestion"):
                venue_suggestions.append({
                    "name": attendee.get("name"),
                    "suggestion": attendee.get("venue_suggestion")
                })
        
        # Get top preferences
        top_preferences = sorted(preference_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Generate mock AI recommendations based on the data
        # In a real implementation, this would call the LLM service
        recommendations = []
        
        # Base recommendation data
        base_recommendations = [
            {
                "name": "Café Central",
                "description": "Perfect for intimate gatherings with confirmed attendees",
                "category": "café",
                "rating": 4.5,
                "price_range": "€€"
            },
            {
                "name": "Park Pavilion",
                "description": "Great outdoor option with indoor backup",
                "category": "outdoor",
                "rating": 4.3,
                "price_range": "€€€"
            },
            {
                "name": "Local Brewery",
                "description": "Casual atmosphere perfect for your group",
                "category": "drinks",
                "rating": 4.6,
                "price_range": "€€"
            }
        ]
        
        # Create AI recommendations with personalized reasoning
        for i, base_rec in enumerate(base_recommendations):
            reasoning = f"Based on {len(confirmed_attendees)} confirmed attendees"
            if top_preferences:
                reasoning += f" and preference for {top_preferences[0][0]}"
            if venue_suggestions:
                reasoning += f". Considers venue suggestions from {len(venue_suggestions)} attendees"
            
            recommendation = AIRecommendation(
                id=str(ObjectId()),
                name=base_rec["name"],
                description=base_rec["description"],
                reasoning=reasoning,
                rating=base_rec["rating"],
                price_range=base_rec["price_range"],
                category=base_rec["category"],
                venue_details={
                    "confirmed_attendees": len(confirmed_attendees),
                    "top_preferences": [pref[0] for pref in top_preferences[:2]],
                    "venue_suggestions_count": len(venue_suggestions)
                }
            )
            recommendations.append(recommendation)
        
        # Update activity with recommendations and new status
        recommendations_data = [rec.model_dump() for rec in recommendations]
        await db.activities.update_one(
            {"_id": ObjectId(activity_id)},
            {
                "$set": {
                    "ai_recommendations": recommendations_data,
                    "status": ActivityStatus.RECOMMENDATIONS_GENERATED,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return RecommendationResponse(
            success=True,
            recommendations=recommendations,
            activity_id=activity_id,
            confirmed_attendees=len(confirmed_attendees),
            metadata={
                "top_preferences": dict(top_preferences),
                "venue_suggestions": venue_suggestions,
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.post("/{activity_id}/finalization-recommendations", response_model=FinalizationRecommendationsResponse)
async def generate_finalization_recommendations(
    activity_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate AI recommendations for final date/venue based on invitee responses.
    
    Only the organizer can request finalization recommendations. This analyzes
    confirmed attendees' preferences and generates personalized recommendations.
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
                detail="Only the organizer can request finalization recommendations"
            )
        
        # Analyze responses to get confirmed attendees
        invitees = activity.get("invitees", [])
        confirmed_attendees = [
            invitee for invitee in invitees
            if invitee.get("response") in ["yes", "maybe"]
        ]
        
        if len(confirmed_attendees) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No confirmed attendees to generate recommendations for"
            )
        
        # Import LLM service here to avoid circular imports
        from backend.services.llm import llm_service
        
        # Generate finalization recommendations using enhanced LLM service
        recommendations_result = await llm_service.generate_finalization_recommendations(
            activity_id=activity_id,
            activity=activity,
            confirmed_attendees=confirmed_attendees,
            organizer_preferences={}  # Could be expanded to include organizer preferences
        )
        
        if not recommendations_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=recommendations_result.get("error", "Failed to generate recommendations")
            )
        
        # Update activity status to indicate finalization is in progress
        await db.activities.update_one(
            {"_id": ObjectId(activity_id)},
            {
                "$set": {
                    "finalization_status": "in_progress",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return FinalizationRecommendationsResponse(
            success=True,
            date_recommendations=recommendations_result.get("date_recommendations", []),
            venue_recommendations=recommendations_result.get("venue_recommendations", []),
            activity_id=activity_id,
            confirmed_attendees=len(confirmed_attendees),
            metadata=recommendations_result.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate finalization recommendations: {str(e)}"
        )


@router.put("/{activity_id}/finalize")
async def finalize_activity_with_details(
    activity_id: str,
    finalization_request: ActivityFinalizationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Finalize activity with confirmed date, time, and venue.
    
    Only the organizer can finalize the activity. This sets the final
    details and updates the activity status to finalized.
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
                detail="Only the organizer can finalize this activity"
            )
        
        # Prepare finalization data
        finalization_data = {
            "finalization_status": "finalized",
            "status": ActivityStatus.FINALIZED,
            "finalization_timestamp": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Add finalized details if provided
        if finalization_request.finalized_date:
            finalization_data["finalized_date"] = finalization_request.finalized_date
        if finalization_request.finalized_time:
            finalization_data["finalized_time"] = finalization_request.finalized_time
        if finalization_request.finalized_venue:
            finalization_data["finalized_venue"] = finalization_request.finalized_venue
        
        # Update activity with finalization data
        await db.activities.update_one(
            {"_id": ObjectId(activity_id)},
            {"$set": finalization_data}
        )
        
        # Get updated activity
        updated_activity = await db.activities.find_one({"_id": ObjectId(activity_id)})
        
        return {
            "message": "Activity finalized successfully",
            "activity_id": activity_id,
            "finalization_status": "finalized",
            "finalized_date": finalization_request.finalized_date.isoformat() if finalization_request.finalized_date else None,
            "finalized_time": finalization_request.finalized_time,
            "finalized_venue": finalization_request.finalized_venue,
            "finalization_timestamp": finalization_data["finalization_timestamp"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize activity: {str(e)}"
        )


@router.post("/{activity_id}/final-invites")
async def send_final_invites(
    activity_id: str,
    invite_request: FinalInvitesRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Send final invites to all confirmed attendees including calendar invites.
    
    Only the organizer can send final invites. This sends final details
    via selected communication channels and creates calendar invites.
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
                detail="Only the organizer can send final invites"
            )
        
        # Check if activity is finalized
        if activity.get("finalization_status") != "finalized":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activity must be finalized before sending final invites"
            )
        
        # Get confirmed attendees
        invitees = activity.get("invitees", [])
        confirmed_attendees = [
            invitee for invitee in invitees
            if invitee.get("response") in ["yes", "maybe"]
        ]
        
        if not confirmed_attendees:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No confirmed attendees to send final invites to"
            )
        
        # Filter invitees if specific list provided
        if invite_request.invitee_list:
            confirmed_attendees = [
                attendee for attendee in confirmed_attendees
                if attendee.get("email") in invite_request.invitee_list
            ]
        
        # Send final invitations
        notification_service = NotificationService()
        email_results = []
        
        for attendee in confirmed_attendees:
            attendee_email = attendee.get("email")
            attendee_name = attendee.get("name")
            
            if not attendee_email or not attendee_name:
                continue
            
            # Get communication preference for this attendee
            preferred_channel = invite_request.communication_preferences.get(
                attendee_email, "email"
            ) if invite_request.communication_preferences else "email"
            
            # Send final invitation based on preferred channel
            invitation_sent = False
            
            if preferred_channel == "email":
                invitation_sent = await notification_service.send_activity_finalization_email(
                    to_email=attendee_email,
                    to_name=attendee_name,
                    organizer_name=current_user.name,
                    activity_title=activity["title"],
                    activity_description=activity.get("description", ""),
                    selected_venue=activity.get("finalized_venue", {}),
                    final_message=invite_request.custom_message,
                    activity_details={
                        "selected_date": activity.get("finalized_date"),
                        "selected_days": activity.get("selected_days", []),
                        "timeframe": activity.get("finalized_time")
                    }
                )
            elif preferred_channel == "sms":
                # TODO: Implement SMS final invite
                invitation_sent = True
                print(f"SMS final invite would be sent to {attendee_name} at {attendee_email}")
            elif preferred_channel == "whatsapp":
                # TODO: Implement WhatsApp final invite
                invitation_sent = True
                print(f"WhatsApp final invite would be sent to {attendee_name} at {attendee_email}")
            
            email_results.append({
                "email": attendee_email,
                "name": attendee_name,
                "channel": preferred_channel,
                "invitation_sent": invitation_sent
            })
            
            # Create in-app notification if the attendee is a registered user
            existing_user = await db.users.find_one({"email": attendee_email})
            if existing_user:
                await notification_service.create_notification(
                    db,
                    str(existing_user["_id"]),
                    f"Final details for {activity['title']} - {activity.get('finalized_venue', {}).get('name', 'venue confirmed')}",
                    "final_invite",
                    {
                        "activity_id": activity_id,
                        "activity_title": activity["title"],
                        "venue_name": activity.get("finalized_venue", {}).get("name", ""),
                        "organizer_name": current_user.name,
                        "finalized_date": activity.get("finalized_date").isoformat() if activity.get("finalized_date") else None,
                        "finalized_time": activity.get("finalized_time")
                    }
                )
        
        # Update activity to mark final invites as sent
        await db.activities.update_one(
            {"_id": ObjectId(activity_id)},
            {
                "$set": {
                    "final_invites_sent": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        successful_invitations = sum(1 for result in email_results if result["invitation_sent"])
        
        return {
            "message": "Final invites sent successfully",
            "activity_id": activity_id,
            "invites_sent": successful_invitations,
            "total_attendees": len(confirmed_attendees),
            "invitation_results": email_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send final invites: {str(e)}"
        )


@router.post("/{activity_id}/add-to-calendar")
async def add_to_calendar(
    activity_id: str,
    calendar_request: CalendarIntegrationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Add finalized activity to organizer's connected calendar.
    
    Only the organizer can add the activity to their calendar.
    Requires existing calendar integration setup.
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
                detail="Only the organizer can add this activity to calendar"
            )
        
        # Check if activity is finalized
        if activity.get("finalization_status") != "finalized":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activity must be finalized before adding to calendar"
            )
        
        # Import Google Calendar service
        from backend.services.google_calendar import google_calendar_service
        
        # Check if user has calendar integration
        user = await db.users.find_one({"_id": ObjectId(current_user.id)})
        calendar_credentials = user.get("google_calendar_credentials")
        
        if not calendar_credentials:
            return {
                "success": False,
                "message": "No calendar integration found. Please connect your calendar first.",
                "calendar_integration_status": "not_connected"
            }
        
        # TODO: Implement actual calendar event creation
        # For now, simulate success
        calendar_integration_status = "integrated"
        
        # Update activity with calendar integration status
        await db.activities.update_one(
            {"_id": ObjectId(activity_id)},
            {
                "$set": {
                    "calendar_integration_status": calendar_integration_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Activity added to calendar successfully",
            "activity_id": activity_id,
            "calendar_integration_status": calendar_integration_status,
            "calendar_provider": calendar_request.calendar_provider
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add activity to calendar: {str(e)}"
        )


@router.get("/{activity_id}/calendar-file")
async def download_calendar_file(
    activity_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate downloadable .ics file for manual calendar import.
    
    Only the organizer can download the calendar file.
    Activity must be finalized.
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
                detail="Only the organizer can download the calendar file"
            )
        
        # Check if activity is finalized
        if activity.get("finalization_status") != "finalized":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activity must be finalized before generating calendar file"
            )
        
        # Generate .ics file content
        from datetime import datetime
        import uuid
        
        # Get activity details
        title = activity.get("title", "Sunnyside Activity")
        description = activity.get("description", "")
        finalized_date = activity.get("finalized_date")
        finalized_time = activity.get("finalized_time", "")
        finalized_venue = activity.get("finalized_venue", {})
        venue_name = finalized_venue.get("name", "")
        venue_address = finalized_venue.get("address", "")
        
        # Create event start and end times
        if finalized_date:
            if isinstance(finalized_date, str):
                event_date = datetime.fromisoformat(finalized_date.replace('Z', '+00:00'))
            else:
                event_date = finalized_date
            
            # If time is specified, parse it
            if finalized_time:
                try:
                    time_parts = finalized_time.split(':')
                    event_date = event_date.replace(
                        hour=int(time_parts[0]),
                        minute=int(time_parts[1]) if len(time_parts) > 1 else 0
                    )
                except:
                    pass  # Use date as-is if time parsing fails
            
            # Set end time (2 hours later by default)
            event_end = event_date.replace(hour=event_date.hour + 2)
        else:
            # Use current date if no finalized date
            event_date = datetime.utcnow()
            event_end = event_date.replace(hour=event_date.hour + 2)
        
        # Format dates for .ics format
        start_time = event_date.strftime('%Y%m%dT%H%M%SZ')
        end_time = event_end.strftime('%Y%m%dT%H%M%SZ')
        created_time = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        
        # Generate unique UID
        event_uid = str(uuid.uuid4())
        
        # Create .ics content
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Sunnyside//Activity Calendar//EN
BEGIN:VEVENT
UID:{event_uid}
DTSTAMP:{created_time}
DTSTART:{start_time}
DTEND:{end_time}
SUMMARY:{title}
DESCRIPTION:{description}
LOCATION:{venue_name}{', ' + venue_address if venue_address else ''}
ORGANIZER:CN={current_user.name}:MAILTO:{current_user.email}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
        
        # Return the .ics file content
        from fastapi.responses import Response
        
        return Response(
            content=ics_content,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.ics"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate calendar file: {str(e)}"
        )

