from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import timedelta, datetime
from bson import ObjectId

from backend.models.user import UserCreate, UserLogin, UserResponse, Token
from backend.models.pending_invitation import InvitationStatus
from backend.auth import (
    authenticate_user,
    create_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    security
)
from backend.services.notifications import NotificationService

router = APIRouter(prefix="/auth", tags=["authentication"])


async def get_database():
    """Dependency to get database connection."""
    import backend.main as main_module
    if main_module.mongodb_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    return main_module.mongodb_client[main_module.DATABASE_NAME]


@router.post("/signup", response_model=Token)
async def signup(
    user_data: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Register a new user.
    
    Creates a new user account with the provided information and returns
    an access token for immediate login. If an invitation token is provided,
    it will automatically connect the user with the person who invited them.
    """
    try:
        # Extract invitation token before creating user
        invitation_token = user_data.invitation_token
        user_dict = user_data.dict()
        # Remove invitation_token from user data as it's not part of the User model
        user_dict.pop('invitation_token', None)
        
        # Create user in database
        user = await create_user(db, user_dict)
        user_id = str(user["_id"])
        
        # Handle invitation token if provided
        if invitation_token:
            try:
                # Find the pending invitation
                invitation = await db.pending_invitations.find_one({
                    "invitation_token": invitation_token,
                    "invitee_email": user_data.email,
                    "status": InvitationStatus.PENDING
                })
                
                if invitation and datetime.utcnow() <= invitation["expires_at"]:
                    # Import here to avoid circular imports
                    from backend.routes.contacts import create_contact_relationship
                    from backend.models.contact import ContactStatus
                    
                    # Create bidirectional contact relationships
                    # From inviter to new user
                    await create_contact_relationship(
                        db,
                        invitation["inviter_user_id"],
                        user_id,
                        invitation.get("message")
                    )
                    
                    # From new user to inviter
                    await create_contact_relationship(
                        db,
                        user_id,
                        invitation["inviter_user_id"]
                    )
                    
                    # Update both to accepted status
                    await db.contacts.update_many(
                        {
                            "$or": [
                                {"user_id": user_id, "contact_user_id": invitation["inviter_user_id"]},
                                {"user_id": invitation["inviter_user_id"], "contact_user_id": user_id}
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
                        f"{user_data.name} accepted your invitation and joined Sunnyside!",
                        "invitation_accepted",
                        {
                            "new_user_name": user_data.name,
                            "new_user_email": user_data.email
                        }
                    )
                    
            except Exception as e:
                # Log the error but don't fail the signup process
                print(f"Error processing invitation token: {str(e)}")
        
        # Send welcome email to the new user
        try:
            from backend.utils.environment import get_frontend_url
            notification_service = NotificationService()
            app_link = get_frontend_url()
            
            await notification_service.send_welcome_email(
                to_email=user_data.email,
                to_name=user_data.name,
                app_link=app_link
            )
        except Exception as e:
            # Log the error but don't fail the signup process
            print(f"Error sending welcome email: {str(e)}")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Authenticate a user and return an access token.
    
    Uses email as username for authentication.
    """
    # Authenticate user
    user = await authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current user details.
    
    Protected endpoint that requires a valid JWT token.
    Returns the current user's profile information.
    """
    current_user = await get_current_user(credentials, db)
    return current_user


@router.get("/test-db")
async def test_database_connection():
    """Test endpoint to check database connection without dependencies."""
    try:
        import backend.main as main_module
        
        status = {
            "database_is_none": main_module.database is None,
            "mongodb_client_is_none": main_module.mongodb_client is None,
            "database_name": main_module.DATABASE_NAME
        }
        
        if main_module.mongodb_client is None:
            return {"error": "mongodb_client is None", "status": status}
        
        # Try to ping the database
        await main_module.mongodb_client.admin.command('ping')
        
        # Get database directly from client
        db = main_module.mongodb_client[main_module.DATABASE_NAME]
        users_collection = db.users
        count = await users_collection.count_documents({})
        
        return {
            "database_available": True,
            "users_count": count,
            "database_name": main_module.DATABASE_NAME,
            "status": status
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}