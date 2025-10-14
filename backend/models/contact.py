from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from datetime import datetime
from enum import Enum

# Custom ObjectId type for Pydantic v2
PyObjectId = Annotated[str, Field(description="MongoDB ObjectId as string")]


class ContactStatus(str, Enum):
    """Status of a contact relationship."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"


class Contact(BaseModel):
    """Model representing a contact relationship between two users."""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="The ID of the user who initiated the contact request")
    contact_user_id: str = Field(..., description="The ID of the user being added as a contact")
    status: ContactStatus = Field(default=ContactStatus.PENDING, description="Status of the contact relationship")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the contact request was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the contact status was last updated")
    nickname: Optional[str] = Field(None, max_length=50, description="Optional nickname for the contact")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about the contact")


class ContactRequest(BaseModel):
    """Model for creating a new contact request."""
    contact_email: str = Field(..., description="Email of the user to add as a contact")
    message: Optional[str] = Field(None, max_length=200, description="Optional message to include with the contact request")


class ContactResponse(BaseModel):
    """Model for responding to a contact request."""
    action: str = Field(..., description="Action to take: 'accept' or 'reject'")


class ContactUpdate(BaseModel):
    """Model for updating contact information."""
    nickname: Optional[str] = Field(None, max_length=50, description="Update nickname for the contact")
    notes: Optional[str] = Field(None, max_length=500, description="Update notes about the contact")


class ContactInfo(BaseModel):
    """Model for returning contact information to the client."""
    id: str
    user_id: str
    contact_user_id: str
    contact_name: str
    contact_email: str
    status: ContactStatus
    created_at: datetime
    updated_at: datetime
    nickname: Optional[str] = None
    notes: Optional[str] = None


class ContactListResponse(BaseModel):
    """Model for returning a list of contacts."""
    contacts: list[ContactInfo]
    total: int