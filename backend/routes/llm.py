from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
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

class RecommendationsRequest(BaseModel):
    """Request model for activity recommendations."""
    query: str = Field(..., description="User query for activity recommendations", min_length=1, max_length=500)
    max_results: int = Field(default=5, description="Maximum number of recommendations to return", ge=1, le=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "something fun to do outdoors",
                "max_results": 5
            }
        }

class RecommendationsResponse(BaseModel):
    """Response model for activity recommendations."""
    success: bool
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    query: str = ""
    retrieved_activities: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "recommendations": [
                    {
                        "title": "Scenic Park Bike Ride",
                        "description": "Enjoy a leisurely bike ride through the local park with beautiful scenery",
                        "category": "outdoor_sports",
                        "duration": "2-3 hours",
                        "difficulty": "moderate",
                        "budget": "free",
                        "indoor_outdoor": "outdoor",
                        "group_size": "1-6 people",
                        "tips": "Bring water and wear comfortable clothing",
                        "venue": {
                            "name": "Central Park Trail",
                            "address": "123 Park Avenue",
                            "link": "https://maps.google.com/central-park-trail",
                            "image_url": "https://example.com/park-trail.jpg"
                        }
                    }
                ],
                "query": "something fun to do outdoors",
                "retrieved_activities": 3,
                "metadata": {
                    "model_used": "mistral-small-latest",
                    "generated_at": "2024-01-14T10:30:00",
                    "rag_enabled": True,
                    "venues_found": 3
                },
                "error": None
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

@router.post("/recommendations", response_model=RecommendationsResponse)
async def get_activity_recommendations(request: RecommendationsRequest) -> RecommendationsResponse:
    """
    Get activity recommendations using RAG pipeline.
    
    This endpoint takes a user's query and returns personalized activity recommendations
    using a Retrieval-Augmented Generation (RAG) approach. It searches through a knowledge
    base of activities and uses an LLM to generate creative, relevant suggestions.
    
    Args:
        request: RecommendationsRequest containing the user's query and preferences
        
    Returns:
        RecommendationsResponse with generated recommendations or error information
        
    Raises:
        HTTPException: If the request is invalid or processing fails
    """
    try:
        # Validate input
        if not request.query or not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )
        
        # Get recommendations using the LLM service
        result = await llm_service.get_recommendations(
            query=request.query.strip(),
            max_results=request.max_results
        )
        
        # Return the result
        return RecommendationsResponse(
            success=result.get("success", False),
            recommendations=result.get("recommendations", []),
            query=result.get("query", request.query),
            retrieved_activities=result.get("retrieved_activities", 0),
            metadata=result.get("metadata", {}),
            error=result.get("error")
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while generating recommendations: {str(e)}"
        )

@router.post("/test-recommendations")
async def test_recommendations():
    """
    Test endpoint for recommendations with a sample query.
    
    Returns:
        RecommendationsResponse with results from a sample query
    """
    sample_query = "something fun to do outdoors with friends"
    
    try:
        result = await llm_service.get_recommendations(
            query=sample_query,
            max_results=3
        )
        
        return RecommendationsResponse(
            success=result.get("success", False),
            recommendations=result.get("recommendations", []),
            query=result.get("query", sample_query),
            retrieved_activities=result.get("retrieved_activities", 0),
            metadata=result.get("metadata", {}),
            error=result.get("error")
        )
    except Exception as e:
        return RecommendationsResponse(
            success=False,
            recommendations=[],
            query=sample_query,
            retrieved_activities=0,
            metadata={},
            error=str(e)
        )