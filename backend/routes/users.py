from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from backend.auth import get_current_user, security

router = APIRouter(prefix="/users", tags=["users"])


async def get_database():
    """Dependency to get database connection."""
    import backend.main as main_module
    if main_module.mongodb_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    return main_module.mongodb_client[main_module.DATABASE_NAME]


@router.delete("/me")
async def delete_account(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete the current user's account and all associated data.
    
    This endpoint permanently deletes:
    - The user record
    - All contact relationships (both directions)
    - All activities organized by the user
    - All pending invitations sent by the user
    - All notifications for the user
    
    This action is irreversible.
    """
    try:
        # Get current user to verify authentication
        current_user = await get_current_user(credentials, db)
        user_id = current_user.id
        user_object_id = ObjectId(user_id)
        
        # Start a transaction to ensure data consistency
        async with await db.client.start_session() as session:
            async with session.start_transaction():
                
                # 1. Delete all contact relationships where user is involved
                # This includes both contacts where user is the initiator and where user is the contact
                contacts_result = await db.contacts.delete_many(
                    {
                        "$or": [
                            {"user_id": user_id},
                            {"contact_user_id": user_id}
                        ]
                    },
                    session=session
                )
                
                # 2. Delete all activities organized by the user
                activities_result = await db.activities.delete_many(
                    {"organizer_id": user_id},
                    session=session
                )
                
                # 3. Remove user from invitees list in activities they were invited to
                # Update activities where user is an invitee
                await db.activities.update_many(
                    {"invitees.id": user_id},
                    {"$pull": {"invitees": {"id": user_id}}},
                    session=session
                )
                
                # 4. Delete all pending invitations sent by the user
                pending_invitations_result = await db.pending_invitations.delete_many(
                    {"inviter_user_id": user_id},
                    session=session
                )
                
                # 5. Delete all notifications for the user
                notifications_result = await db.notifications.delete_many(
                    {"user_id": user_object_id},
                    session=session
                )
                
                # 6. Finally, delete the user record itself
                user_result = await db.users.delete_one(
                    {"_id": user_object_id},
                    session=session
                )
                
                # Verify that the user was actually deleted
                if user_result.deleted_count == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
        
        # Return confirmation with deletion statistics
        return {
            "message": "Account successfully deleted",
            "deleted_data": {
                "user": user_result.deleted_count,
                "contacts": contacts_result.deleted_count,
                "activities": activities_result.deleted_count,
                "pending_invitations": pending_invitations_result.deleted_count,
                "notifications": notifications_result.deleted_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like authentication errors)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )