from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Annotated
from bson import ObjectId
from datetime import datetime
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
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


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
    
    # Invitees and responses
    invitees: List[Invitee] = Field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


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
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


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


class ActivitySummaryResponse(BaseModel):
    """Model for activity summary response."""
    activity: ActivityResponse
    summary: Dict[str, Any]