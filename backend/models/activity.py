from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Annotated
from bson import ObjectId
from datetime import datetime, timezone
from enum import Enum


# Custom ObjectId type for Pydantic v2
PyObjectId = Annotated[str, Field(description="MongoDB ObjectId as string")]


class ActivityStatus(str, Enum):
    PLANNING = "planning"
    WEATHER_PLANNING = "weather-planning"
    INVITATIONS_SENT = "invitations-sent"
    RESPONSES_COLLECTED = "responses-collected"
    READY_FOR_RECOMMENDATIONS = "ready-for-recommendations"
    RECOMMENDATIONS_GENERATED = "recommendations-generated"
    FINALIZED = "finalized"


class InviteeResponse(str, Enum):
    PENDING = "pending"
    YES = "yes"
    NO = "no"
    MAYBE = "maybe"


class Invitee(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, description="User ID if registered user, or new ObjectId for guest")
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(...)
    response: InviteeResponse = Field(default=InviteeResponse.PENDING)
    availability_note: Optional[str] = Field(None, max_length=500)
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    venue_suggestion: Optional[str] = Field(None, max_length=200)
    previous_response: Optional[InviteeResponse] = Field(None, description="Previous response before change")


class ActivitySuggestion(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    category: str = Field(..., max_length=100)
    duration: str = Field(..., max_length=100)
    difficulty: str = Field(..., max_length=50)
    budget: str = Field(..., max_length=50)
    indoor_outdoor: str = Field(..., max_length=50)
    group_size: str = Field(..., max_length=100)
    weather_considerations: Optional[str] = Field(None, max_length=500)
    tips: str = Field(..., max_length=500)
    is_custom: Optional[bool] = Field(default=False)


class AIRecommendation(BaseModel):
    id: str = Field(..., description="Unique identifier for the recommendation")
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    reasoning: str = Field(..., max_length=500, description="AI reasoning for this recommendation")
    rating: Optional[float] = Field(None, ge=0, le=5)
    price_range: Optional[str] = Field(None, max_length=50)
    category: str = Field(..., max_length=100)
    venue_details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class WeatherData(BaseModel):
    date: datetime
    temperature: Optional[float] = None
    condition: Optional[str] = None
    precipitation_chance: Optional[float] = None
    description: Optional[str] = None


class Activity(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organizer_id: PyObjectId = Field(..., description="ID of the user who created the activity")
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: ActivityStatus = Field(default=ActivityStatus.PLANNING)
    
    # Activity details from creation form
    timeframe: Optional[str] = Field(None, max_length=100)
    group_size: Optional[str] = Field(None, max_length=50)
    activity_type: Optional[str] = Field(None, max_length=100)
    weather_preference: Optional[str] = Field(None, max_length=50)
    selected_date: Optional[datetime] = Field(None)
    selected_days: Optional[List[str]] = Field(default_factory=list)
    deadline: Optional[datetime] = Field(None, description="Deadline for invitee responses")
    
    # Weather and planning data
    weather_data: Optional[List[WeatherData]] = Field(default_factory=list)
    
    # Activity suggestions
    suggestions: Optional[List[ActivitySuggestion]] = Field(default_factory=list)
    
    # AI recommendations based on responses
    ai_recommendations: Optional[List[AIRecommendation]] = Field(default_factory=list)
    selected_recommendation: Optional[AIRecommendation] = Field(None)
    
    # Finalization fields
    finalization_status: Optional[str] = Field(default="pending", description="Finalization status: pending, in_progress, finalized")
    finalized_date: Optional[datetime] = Field(None, description="Final confirmed date for the activity")
    finalized_time: Optional[str] = Field(None, description="Final confirmed time for the activity")
    finalized_venue: Optional[Dict[str, Any]] = Field(None, description="Final confirmed venue details")
    finalization_timestamp: Optional[datetime] = Field(None, description="When the activity was finalized")
    final_invites_sent: Optional[bool] = Field(default=False, description="Whether final invites have been sent")
    calendar_integration_status: Optional[str] = Field(default="not_integrated", description="Calendar integration status")
    
    # Invitees and responses
    invitees: List[Invitee] = Field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActivityCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    timeframe: Optional[str] = Field(None, max_length=100)
    group_size: Optional[str] = Field(None, max_length=50, alias="groupSize")
    activity_type: Optional[str] = Field(None, max_length=100, alias="activityType")
    weather_preference: Optional[str] = Field(None, max_length=50, alias="weatherPreference")
    selected_date: Optional[datetime] = Field(None, alias="selectedDate")
    deadline: Optional[datetime] = Field(None, description="Deadline for invitee responses")


class ActivityUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ActivityStatus] = None
    selected_date: Optional[datetime] = None
    selected_days: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    weather_data: Optional[List[WeatherData]] = None
    invitees: Optional[List[Invitee]] = None
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActivityResponse(BaseModel):
    id: str
    organizer_id: str
    organizer_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: ActivityStatus
    timeframe: Optional[str] = None
    group_size: Optional[str] = None
    activity_type: Optional[str] = None
    weather_preference: Optional[str] = None
    selected_date: Optional[datetime] = None
    selected_days: List[str] = []
    deadline: Optional[datetime] = None
    weather_data: List[WeatherData] = []
    suggestions: List[ActivitySuggestion] = []
    ai_recommendations: List[AIRecommendation] = []
    selected_recommendation: Optional[AIRecommendation] = None
    invitees: List[Invitee] = []
    created_at: datetime
    updated_at: datetime


class InviteGuestsRequest(BaseModel):
    invitees: List[Dict[str, str]] = Field(..., description="List of invitees with name and email")
    custom_message: Optional[str] = Field(None, max_length=500)
    channel: Optional[str] = Field(default="email", description="Communication channel: email, whatsapp, or sms")


class GuestResponseRequest(BaseModel):
    response: InviteeResponse
    availability_note: Optional[str] = Field(None, max_length=500)
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    venue_suggestion: Optional[str] = Field(None, max_length=200)


class UserResponseRequest(BaseModel):
    """Model for registered user response submission."""
    response: InviteeResponse = Field(..., description="User's response: yes, no, maybe")
    availability_note: Optional[str] = Field(None, max_length=500, alias="availabilityNote")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    venue_suggestion: Optional[str] = Field(None, max_length=200, alias="venueSuggestion")


class RecommendationRequest(BaseModel):
    """Request model for generating AI recommendations based on responses."""
    activity_id: str = Field(..., description="Activity ID to generate recommendations for")
    max_recommendations: Optional[int] = Field(default=3, ge=1, le=10)


class RecommendationResponse(BaseModel):
    """Response model for AI recommendations."""
    success: bool
    recommendations: List[AIRecommendation] = []
    activity_id: str
    confirmed_attendees: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class FinalizeActivityRequest(BaseModel):
    """Request model for finalizing activity with selected recommendation."""
    recommendation_id: str = Field(..., description="ID of the selected recommendation")
    final_message: Optional[str] = Field(None, max_length=500, description="Final message to send to attendees")


class FinalizationRecommendationsRequest(BaseModel):
    """Request model for generating finalization recommendations."""
    activity_id: str = Field(..., description="Activity ID to generate finalization recommendations for")


class FinalizationRecommendation(BaseModel):
    """Model for finalization recommendation (date/venue)."""
    id: str = Field(..., description="Unique identifier for the recommendation")
    type: str = Field(..., description="Type of recommendation: 'date' or 'venue'")
    title: str = Field(..., description="Title of the recommendation")
    description: str = Field(..., description="Description of the recommendation")
    reasoning: str = Field(..., description="AI reasoning for this recommendation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class FinalizationRecommendationsResponse(BaseModel):
    """Response model for finalization recommendations."""
    success: bool
    date_recommendations: List[FinalizationRecommendation] = []
    venue_recommendations: List[FinalizationRecommendation] = []
    activity_id: str
    confirmed_attendees: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ActivityFinalizationRequest(BaseModel):
    """Request model for finalizing activity with final details."""
    finalized_date: Optional[datetime] = Field(None, description="Final confirmed date")
    finalized_time: Optional[str] = Field(None, description="Final confirmed time")
    finalized_venue: Optional[Dict[str, Any]] = Field(None, description="Final venue details")
    final_message: Optional[str] = Field(None, max_length=500, description="Final message to attendees")


class FinalInvitesRequest(BaseModel):
    """Request model for sending final invites."""
    communication_preferences: Optional[Dict[str, str]] = Field(default_factory=dict, description="Communication channel preferences per invitee")
    custom_message: Optional[str] = Field(None, max_length=500, description="Custom message for final invites")
    invitee_list: Optional[List[str]] = Field(None, description="Specific invitees to send to (if not all)")


class CalendarIntegrationRequest(BaseModel):
    """Request model for calendar integration."""
    calendar_provider: Optional[str] = Field(default="google", description="Calendar provider (google, outlook, etc.)")
    event_details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event details")


class ActivitySummaryResponse(BaseModel):
    """Model for activity summary response."""
    activity: ActivityResponse
    summary: Dict[str, Any]