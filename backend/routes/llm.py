from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from ..services.llm import llm_service

router = APIRouter(prefix="/llm", tags=["llm"])

class ParseIntentRequest(BaseModel):
    """Request model for intent parsing."""
    text: str = Field(..., description="User input text to parse for intent", min_length=1, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Let's go for a bike ride tomorrow afternoon"
            }
        }

class ParseIntentResponse(BaseModel):
    """Response model for intent parsing."""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "activity": {
                        "type": "outdoor_sports",
                        "description": "bike ride",
                        "specific_activity": "bike ride",
                        "confidence": 0.95
                    },
                    "datetime": {
                        "date": "2024-01-15",
                        "time": "14:00",
                        "duration": "2 hours",
                        "flexibility": "preferred",
                        "relative_time": "tomorrow afternoon"
                    },
                    "location": {
                        "type": "unspecified",
                        "details": None,
                        "indoor_outdoor": "outdoor",
                        "travel_required": True
                    },
                    "participants": {
                        "count": None,
                        "type": "unknown",
                        "specific_people": []
                    },
                    "requirements": ["bicycle", "good weather"],
                    "mood": "energetic",
                    "budget": {
                        "level": "free",
                        "specific_amount": None
                    },
                    "metadata": {
                        "parsed_at": "2024-01-14T10:30:00",
                        "model_used": "mistral-small-latest",
                        "processing_version": "1.0"
                    }
                },
                "error": None
            }
        }

@router.post("/parse-intent", response_model=ParseIntentResponse)
async def parse_intent(request: ParseIntentRequest) -> ParseIntentResponse:
    """
    Parse user intent from natural language input.
    
    This endpoint takes a natural language description of an activity or plan
    and returns structured information about the user's intent, including:
    - Activity type and details
    - Date and time preferences
    - Location requirements
    - Participant information
    - Required resources
    - Mood and budget considerations
    
    Args:
        request: ParseIntentRequest containing the user's text input
        
    Returns:
        ParseIntentResponse with structured intent data or error information
        
    Raises:
        HTTPException: If the request is invalid or processing fails
    """
    try:
        # Validate input
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text input cannot be empty"
            )
        
        # Parse the intent using the LLM service
        parsed_intent = await llm_service.parse_intent(request.text.strip())
        
        # Check if parsing was successful
        if not parsed_intent.get("success", False):
            return ParseIntentResponse(
                success=False,
                data={},
                error=parsed_intent.get("error", "Failed to parse intent")
            )
        
        # Return successful response
        return ParseIntentResponse(
            success=True,
            data=parsed_intent,
            error=None
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while parsing intent: {str(e)}"
        )

@router.get("/health")
async def llm_health_check():
    """
    Health check endpoint for the LLM service.
    
    Returns:
        Dict with service status and configuration info
    """
    try:
        # Check if the LLM service is properly configured
        has_api_key = bool(llm_service.api_key)
        
        return {
            "status": "ok",
            "service": "llm",
            "configured": has_api_key,
            "model": llm_service.model if has_api_key else None
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "llm",
            "configured": False,
            "error": str(e)
        }

@router.post("/test-parse")
async def test_parse_intent():
    """
    Test endpoint with a sample input for development and testing purposes.
    
    Returns:
        ParseIntentResponse with results from parsing a sample text
    """
    sample_text = "Let's go for a bike ride tomorrow afternoon with friends"
    
    try:
        parsed_intent = await llm_service.parse_intent(sample_text)
        
        return ParseIntentResponse(
            success=True,
            data=parsed_intent,
            error=None
        )
    except Exception as e:
        return ParseIntentResponse(
            success=False,
            data={},
            error=str(e)
        )