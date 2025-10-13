from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import os

from backend.models.user import User, UserResponse

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRES_IN", "3600")) // 60  # Convert seconds to minutes

# Security scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[dict]:
    """Get a user by email from the database."""
    user = await db.users.find_one({"email": email})
    return user


async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[dict]:
    """Authenticate a user by email and password."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = None
) -> UserResponse:
    """Get the current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    if not ObjectId.is_valid(user_id):
        raise credentials_exception
        
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
    
    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        location=user.get("location"),
        preferences=user.get("preferences", [])
    )


async def create_user(db: AsyncIOMotorDatabase, user_data: dict) -> dict:
    """Create a new user in the database."""
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data["email"])
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    user_data["created_at"] = datetime.utcnow()
    
    # Insert user into database
    result = await db.users.insert_one(user_data)
    
    # Return the created user
    user = await db.users.find_one({"_id": result.inserted_id})
    return user