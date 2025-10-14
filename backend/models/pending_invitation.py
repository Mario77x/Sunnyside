from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from datetime import datetime, timedelta
from enum import Enum

# Custom ObjectId type for Pydantic v2
PyObjectId = Annotated[str, Field(description="MongoDB ObjectId as string")]


class InvitationType(str, Enum):
    """Type of invitation."""
    CONTACT_REQUEST = "contact_request"
    ACCOUNT_INVITATION = "account_invitation"


class InvitationStatus(str, Enum):
    """Status of a pending invitation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PendingInvitation(BaseModel):
    """Model representing a pending invitation to a non-existing user."""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    inviter_user_id: str = Field(..., description="The ID of the user sending the invitation")
    invitee_email: str = Field(..., description="Email of the person being invited")
    invitee_name: Optional[str] = Field(None, description="Name of the person being invited")
    invitation_type: InvitationType = Field(..., description="Type of invitation")
    status: InvitationStatus = Field(default=InvitationStatus.PENDING, description="Status of the invitation")
    message: Optional[str] = Field(None, max_length=500, description="Optional message from the inviter")
    invitation_token: str = Field(..., description="Unique token for the invitation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the invitation was created")
    expires_at: datetime = Field(..., description="When the invitation expires")
    accepted_at: Optional[datetime] = Field(None, description="When the invitation was accepted")
    
    @classmethod
    def create_with_expiry(
        cls,
        inviter_user_id: str,
        invitee_email: str,
        invitation_type: InvitationType,
        invitation_token: str,
        invitee_name: Optional[str] = None,
        message: Optional[str] = None,
        expiry_days: int = 30
    ):
        """Create a pending invitation with automatic expiry date."""
        return cls(
            inviter_user_id=inviter_user_id,
            invitee_email=invitee_email,
            invitee_name=invitee_name,
            invitation_type=invitation_type,
            invitation_token=invitation_token,
            message=message,
            expires_at=datetime.utcnow() + timedelta(days=expiry_days),
            accepted_at=None
        )


class PendingInvitationResponse(BaseModel):
    """Response model for pending invitation operations."""
    id: str
    inviter_user_id: str
    invitee_email: str
    invitee_name: Optional[str]
    invitation_type: InvitationType
    status: InvitationStatus
    message: Optional[str]
    created_at: datetime
    expires_at: datetime