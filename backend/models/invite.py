from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from backend.models.activity import InviteeResponse


class GuestResponseRequest(BaseModel):
    """Model for guest response submission."""
    response: InviteeResponse = Field(..., description="Guest's response: yes, no, maybe")
    availability_note: Optional[str] = Field(None, max_length=500, alias="availabilityNote")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    venue_suggestion: Optional[str] = Field(None, max_length=200, alias="venueSuggestion")
    guest_id: Optional[str] = Field(None, description="Unique identifier for the guest")


class PublicActivityResponse(BaseModel):
    """Simplified, public version of activity details for guests."""
    id: str
    title: str
    description: Optional[str] = None
    organizer_name: str
    selected_date: Optional[datetime] = None
    selected_days: list[str] = []
    activity_type: Optional[str] = None
    weather_preference: Optional[str] = None
    timeframe: Optional[str] = None
    group_size: Optional[str] = None
    deadline: Optional[datetime] = None
    # Note: We don't expose sensitive information like organizer_id, invitees list, etc.


class GuestResponseSubmission(BaseModel):
    """Response model for successful guest response submission."""
    message: str
    response_recorded: InviteeResponse
    guest_name: Optional[str] = None