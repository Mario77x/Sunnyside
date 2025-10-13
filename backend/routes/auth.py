from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import timedelta

from backend.models.user import UserCreate, UserLogin, UserResponse, Token
from backend.auth import (
    authenticate_user,
    create_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    security
)

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
    an access token for immediate login.
    """
    try:
        # Create user in database
        user = await create_user(db, user_data.dict())
        
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