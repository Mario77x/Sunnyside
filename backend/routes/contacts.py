from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import secrets
import os

from backend.models.contact import (
    Contact,
    ContactRequest,
    ContactResponse,
    ContactUpdate,
    ContactInfo,
    ContactListResponse,
    ContactStatus
)
from backend.models.pending_invitation import (
    PendingInvitation,
    InvitationType,
    InvitationStatus
)
from backend.models.user import UserResponse
from backend.auth import get_current_user, security
from backend.services.notifications import NotificationService

from backend.dependencies import get_database

router = APIRouter(prefix="/contacts", tags=["contacts"])


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> dict:
    """Get user by email address."""
    user = await db.users.find_one({"email": email})
    return user


async def create_contact_relationship(db: AsyncIOMotorDatabase, user_id: str, contact_user_id: str, message: Optional[str] = None) -> dict:
    """Create a new contact relationship in the database."""
    contact_data = {
        "user_id": user_id,
        "contact_user_id": contact_user_id,
        "status": ContactStatus.PENDING,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "nickname": None,
        "notes": message
    }
    
    result = await db.contacts.insert_one(contact_data)
    contact = await db.contacts.find_one({"_id": result.inserted_id})
    return contact


async def get_contact_info_with_user_details(db: AsyncIOMotorDatabase, contact: dict) -> ContactInfo:
    """Convert contact document to ContactInfo with user details."""
    # Get contact user details
    contact_user = await db.users.find_one({"_id": ObjectId(contact["contact_user_id"])})
    
    return ContactInfo(
        id=str(contact["_id"]),
        user_id=contact["user_id"],
        contact_user_id=contact["contact_user_id"],
        contact_name=contact_user["name"] if contact_user else "Unknown User",
        contact_email=contact_user["email"] if contact_user else "unknown@email.com",
        status=contact["status"],
        created_at=contact["created_at"],
        updated_at=contact["updated_at"],
        nickname=contact.get("nickname"),
        notes=contact.get("notes")
    )


@router.post("/request", response_model=dict)
async def send_contact_request(
    contact_request: ContactRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Send a contact request to another user by email.
    
    Privacy-preserving: Does not reveal whether the user exists or not.
    - If user exists: Creates contact request and sends in-app notification + email
    - If user doesn't exist: Creates pending invitation and sends signup invitation email
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Check if trying to add themselves
        if contact_request.contact_email == current_user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add yourself as a contact"
            )
        
        # Initialize notification service
        notification_service = NotificationService()
        
        # Check if the user exists (but don't reveal this to the requester)
        contact_user = await get_user_by_email(db, contact_request.contact_email)
        
        if contact_user:
            # User exists - handle as existing user contact request
            contact_user_id = str(contact_user["_id"])
            
            # Check if contact relationship already exists (in either direction)
            existing_contact = await db.contacts.find_one({
                "$or": [
                    {"user_id": current_user.id, "contact_user_id": contact_user_id},
                    {"user_id": contact_user_id, "contact_user_id": current_user.id}
                ]
            })
            
            if existing_contact:
                if existing_contact["status"] == ContactStatus.ACCEPTED:
                    # Return generic success message to not reveal existing relationship
                    return {
                        "message": "Contact request sent successfully",
                        "status": "sent"
                    }
                elif existing_contact["status"] == ContactStatus.PENDING:
                    # Return generic success message to not reveal pending status
                    return {
                        "message": "Contact request sent successfully",
                        "status": "sent"
                    }
                elif existing_contact["status"] == ContactStatus.BLOCKED:
                    # Return generic success message to not reveal blocked status
                    return {
                        "message": "Contact request sent successfully",
                        "status": "sent"
                    }
            
            # Create the contact relationship
            contact = await create_contact_relationship(
                db,
                current_user.id,
                contact_user_id,
                contact_request.message
            )
            
            # Send in-app notification
            await notification_service.create_notification(
                db,
                contact_user_id,
                f"{current_user.name} wants to connect with you",
                "contact_request",
                {
                    "contact_id": str(contact["_id"]),
                    "requester_name": current_user.name,
                    "requester_email": current_user.email,
                    "message": contact_request.message
                }
            )
            
            # Send email notification to existing user
            # Temporary solution, sending links to local env during PoC testing, to be removed before launch
            from backend.utils.environment import get_frontend_url
            app_link = get_frontend_url()
            await notification_service.send_contact_request_email(
                contact_user["email"],
                contact_user["name"],
                current_user.name,
                contact_request.message,
                app_link
            )
            
        else:
            # User doesn't exist - handle as invitation to join
            
            # Check if there's already a pending invitation for this email from this user
            existing_invitation = await db.pending_invitations.find_one({
                "inviter_user_id": current_user.id,
                "invitee_email": contact_request.contact_email,
                "invitation_type": InvitationType.CONTACT_REQUEST,
                "status": InvitationStatus.PENDING
            })
            
            if existing_invitation:
                # Return generic success message to not reveal existing invitation
                return {
                    "message": "Contact request sent successfully",
                    "status": "sent"
                }
            
            # Generate unique invitation token
            invitation_token = secrets.token_urlsafe(32)
            
            # Create pending invitation
            pending_invitation = PendingInvitation.create_with_expiry(
                inviter_user_id=current_user.id,
                invitee_email=contact_request.contact_email,
                invitation_type=InvitationType.CONTACT_REQUEST,
                invitation_token=invitation_token,
                message=contact_request.message,
                expiry_days=30
            )
            
            # Save to database
            invitation_data = pending_invitation.model_dump(exclude={"id"})
            await db.pending_invitations.insert_one(invitation_data)
            
            # Send invitation email
            # Temporary solution, sending links to local env during PoC testing, to be removed before launch
            from backend.utils.environment import get_signup_link
            signup_link = get_signup_link(invitation_token)
            await notification_service.send_account_invitation_email(
                contact_request.contact_email,
                None,  # We don't know their name
                current_user.name,
                invitation_token,
                contact_request.message,
                signup_link
            )
        
        # Always return the same generic success message regardless of whether user exists
        return {
            "message": "Contact request sent successfully",
            "status": "sent"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send contact request: {str(e)}"
        )


@router.post("/{contact_id}/respond", response_model=dict)
async def respond_to_contact_request(
    contact_id: str,
    response: ContactResponse,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Accept or reject a contact request.
    
    Only the recipient of the contact request can respond to it.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Validate contact ID
        if not ObjectId.is_valid(contact_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid contact ID"
            )
        
        # Find the contact request
        contact = await db.contacts.find_one({"_id": ObjectId(contact_id)})
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact request not found"
            )
        
        # Check if current user is the recipient
        if contact["contact_user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only respond to contact requests sent to you"
            )
        
        # Check if request is still pending
        if contact["status"] != ContactStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This contact request has already been responded to"
            )
        
        # Validate response action
        if response.action not in ["accept", "reject"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'accept' or 'reject'"
            )
        
        # Update contact status
        new_status = ContactStatus.ACCEPTED if response.action == "accept" else ContactStatus.BLOCKED
        
        await db.contacts.update_one(
            {"_id": ObjectId(contact_id)},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # If accepted, create the reciprocal relationship
        if response.action == "accept":
            # Check if reciprocal relationship already exists
            reciprocal_contact = await db.contacts.find_one({
                "user_id": current_user.id,
                "contact_user_id": contact["user_id"]
            })
            
            if not reciprocal_contact:
                await create_contact_relationship(
                    db,
                    current_user.id,
                    contact["user_id"]
                )
                # Update the reciprocal relationship to accepted status
                await db.contacts.update_one(
                    {"user_id": current_user.id, "contact_user_id": contact["user_id"]},
                    {"$set": {"status": ContactStatus.ACCEPTED, "updated_at": datetime.utcnow()}}
                )
        
        action_message = "accepted" if response.action == "accept" else "rejected"
        return {
            "message": f"Contact request {action_message} successfully",
            "status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to respond to contact request: {str(e)}"
        )


@router.get("", response_model=ContactListResponse)
async def get_contacts(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all contacts for the current user.
    
    Returns only accepted contacts.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Find all accepted contacts for the user
        cursor = db.contacts.find({
            "user_id": current_user.id,
            "status": ContactStatus.ACCEPTED
        }).sort("created_at", -1)
        
        contacts = await cursor.to_list(length=None)
        
        # Convert to ContactInfo with user details
        contact_infos = []
        for contact in contacts:
            contact_info = await get_contact_info_with_user_details(db, contact)
            contact_infos.append(contact_info)
        
        return ContactListResponse(
            contacts=contact_infos,
            total=len(contact_infos)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve contacts: {str(e)}"
        )


@router.get("/requests", response_model=ContactListResponse)
async def get_contact_requests(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all pending contact requests for the current user.
    
    Returns contact requests that the user has received and can respond to.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Find all pending contact requests sent to the user
        cursor = db.contacts.find({
            "contact_user_id": current_user.id,
            "status": ContactStatus.PENDING
        }).sort("created_at", -1)
        
        requests = await cursor.to_list(length=None)
        
        # Convert to ContactInfo with user details
        request_infos = []
        for request in requests:
            # For requests, we need to get the sender's details
            sender_user = await db.users.find_one({"_id": ObjectId(request["user_id"])})
            
            request_info = ContactInfo(
                id=str(request["_id"]),
                user_id=request["user_id"],
                contact_user_id=request["contact_user_id"],
                contact_name=sender_user["name"] if sender_user else "Unknown User",
                contact_email=sender_user["email"] if sender_user else "unknown@email.com",
                status=request["status"],
                created_at=request["created_at"],
                updated_at=request["updated_at"],
                nickname=request.get("nickname"),
                notes=request.get("notes")
            )
            request_infos.append(request_info)
        
        return ContactListResponse(
            contacts=request_infos,
            total=len(request_infos)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve contact requests: {str(e)}"
        )


@router.put("/{contact_id}", response_model=ContactInfo)
async def update_contact(
    contact_id: str,
    contact_update: ContactUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update contact information (nickname and notes).
    
    Only the owner of the contact relationship can update it.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Validate contact ID
        if not ObjectId.is_valid(contact_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid contact ID"
            )
        
        # Find the contact
        contact = await db.contacts.find_one({"_id": ObjectId(contact_id)})
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        # Check if current user owns this contact relationship
        if contact["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own contacts"
            )
        
        # Prepare update data
        update_data = contact_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update contact in database
            await db.contacts.update_one(
                {"_id": ObjectId(contact_id)},
                {"$set": update_data}
            )
        
        # Get updated contact
        updated_contact = await db.contacts.find_one({"_id": ObjectId(contact_id)})
        
        # Convert to ContactInfo with user details
        return await get_contact_info_with_user_details(db, updated_contact)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact: {str(e)}"
        )


@router.delete("/{contact_id}", response_model=dict)
async def remove_contact(
    contact_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Remove a contact relationship.
    
    This removes both sides of the contact relationship.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Validate contact ID
        if not ObjectId.is_valid(contact_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid contact ID"
            )
        
        # Find the contact
        contact = await db.contacts.find_one({"_id": ObjectId(contact_id)})
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        # Check if current user owns this contact relationship
        if contact["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only remove your own contacts"
            )
        
        # Remove the contact relationship
        await db.contacts.delete_one({"_id": ObjectId(contact_id)})
        
        # Also remove the reciprocal relationship if it exists
        await db.contacts.delete_one({
            "user_id": contact["contact_user_id"],
            "contact_user_id": contact["user_id"]
        })
        
        return {
            "message": "Contact removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove contact: {str(e)}"
        )


@router.post("/accept-invitation/{token}", response_model=dict)
async def accept_invitation_token(
    token: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Accept a pending invitation using the invitation token.
    
    This endpoint is called when a new user signs up with an invitation token
    and wants to automatically connect with the person who invited them.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Find the pending invitation
        invitation = await db.pending_invitations.find_one({
            "invitation_token": token,
            "invitee_email": current_user.email,
            "status": InvitationStatus.PENDING
        })
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found or already processed"
            )
        
        # Check if invitation has expired
        if datetime.utcnow() > invitation["expires_at"]:
            # Mark as expired
            await db.pending_invitations.update_one(
                {"_id": invitation["_id"]},
                {"$set": {"status": InvitationStatus.EXPIRED}}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has expired"
            )
        
        # Get the inviter user
        inviter = await db.users.find_one({"_id": ObjectId(invitation["inviter_user_id"])})
        if not inviter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inviter not found"
            )
        
        # Check if contact relationship already exists
        existing_contact = await db.contacts.find_one({
            "$or": [
                {"user_id": current_user.id, "contact_user_id": invitation["inviter_user_id"]},
                {"user_id": invitation["inviter_user_id"], "contact_user_id": current_user.id}
            ]
        })
        
        if not existing_contact:
            # Create bidirectional contact relationships
            # From inviter to new user
            await create_contact_relationship(
                db,
                invitation["inviter_user_id"],
                current_user.id,
                invitation.get("message")
            )
            
            # From new user to inviter (accepted)
            contact = await create_contact_relationship(
                db,
                current_user.id,
                invitation["inviter_user_id"]
            )
            
            # Update both to accepted status
            await db.contacts.update_many(
                {
                    "$or": [
                        {"user_id": current_user.id, "contact_user_id": invitation["inviter_user_id"]},
                        {"user_id": invitation["inviter_user_id"], "contact_user_id": current_user.id}
                    ]
                },
                {"$set": {"status": ContactStatus.ACCEPTED, "updated_at": datetime.utcnow()}}
            )
        
        # Mark invitation as accepted
        await db.pending_invitations.update_one(
            {"_id": invitation["_id"]},
            {
                "$set": {
                    "status": InvitationStatus.ACCEPTED,
                    "accepted_at": datetime.utcnow()
                }
            }
        )
        
        # Create notification for the inviter
        notification_service = NotificationService()
        await notification_service.create_notification(
            db,
            invitation["inviter_user_id"],
            f"{current_user.name} accepted your invitation and joined Sunnyside!",
            "invitation_accepted",
            {
                "new_user_name": current_user.name,
                "new_user_email": current_user.email
            }
        )
        
        return {
            "message": f"Successfully connected with {inviter['name']}!",
            "inviter_name": inviter["name"],
            "status": "accepted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept invitation: {str(e)}"
        )


@router.get("/pending-invitations", response_model=List[dict])
async def get_pending_invitations(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all pending invitations sent by the current user.
    
    This allows users to see who they've invited that hasn't joined yet.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials, db)
        
        # Find all pending invitations sent by this user
        cursor = db.pending_invitations.find({
            "inviter_user_id": current_user.id,
            "status": InvitationStatus.PENDING
        }).sort("created_at", -1)
        
        invitations = await cursor.to_list(length=None)
        
        # Convert to response format
        result = []
        for invitation in invitations:
            result.append({
                "id": str(invitation["_id"]),
                "invitee_email": invitation["invitee_email"],
                "invitee_name": invitation.get("invitee_name"),
                "invitation_type": invitation["invitation_type"],
                "message": invitation.get("message"),
                "created_at": invitation["created_at"],
                "expires_at": invitation["expires_at"]
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pending invitations: {str(e)}"
        )