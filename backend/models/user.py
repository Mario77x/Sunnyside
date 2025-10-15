from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Annotated
from bson import ObjectId
from datetime import datetime


# Custom ObjectId type for Pydantic v2
PyObjectId = Annotated[str, Field(description="MongoDB ObjectId as string")]


class User(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(...)
    hashed_password: str = Field(...)
    location: Optional[str] = Field(None, max_length=100)
    preferences: Optional[List[str]] = Field(default_factory=list)
    role: str = Field(default="user", description="User role (user, admin, etc.)")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    google_calendar_integrated: bool = Field(default=False)
    google_calendar_credentials: Optional[dict] = Field(default=None)


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    location: Optional[str] = Field(None, max_length=100)
    preferences: Optional[List[str]] = Field(default_factory=list)
    role: Optional[str] = Field(default="user", description="User role (user, admin, etc.)")
    invitation_token: Optional[str] = Field(None, description="Optional invitation token for automatic contact connection")


class UserLogin(BaseModel):
    username: str  # This will be the email
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    location: Optional[str] = None
    preferences: List[str] = []
    role: str = "user"
    google_calendar_integrated: bool = False
    google_calendar_credentials: Optional[dict] = None


class Token(BaseModel):
    access_token: str
    token_type: str